"""lambda funtion to cancel trips"""
from datetime import datetime
from datetime import timedelta
import boto3
from botocore.exceptions import ClientError
from src.common_tools.payload_parser import success_return_parser, error_return_parser
from src.trips_tools.messaging_tools import send_push_notification
from src.trips_tools.seats_tools import get_updated_seats

TRIPS_TABLE = "trips"
USERS_TABLE = "users"
USER_DATA_TABLE = "user_data"
USER_REQUESTS_TABLE = "user_requests"
USER_RESERVATIONS_TABLE = "user_reservations"
TRIPS_SESSIONS_TABLE = "trips_sessions"
TRIPS_RESERVATIONS_TABLE = "trips_reservations"
CHAT_TABLE = "chat"

dynamodb = boto3.client("dynamodb")
trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USER_REQUESTS_TABLE)
user_reservations_table = boto3.resource("dynamodb").Table(USER_RESERVATIONS_TABLE)
trips_sessions_table = boto3.resource("dynamodb").Table(TRIPS_SESSIONS_TABLE)
trips_reservations_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS_TABLE)
chat_table = boto3.resource("dynamodb").Table(CHAT_TABLE)

def check_time(departure_time):
    """function to check if request fits cancelation policy"""
    current_time = datetime.now().isoformat(timespec="seconds")
    current_time_obj = datetime.strptime(current_time, "%Y-%m-%dT%H:%M:%S")
    departure_time_obj = datetime.strptime(departure_time, "%Y-%m-%dT%H:%M:%S")
    one_hour_before = departure_time_obj - timedelta(hours=1)
    if current_time_obj <= one_hour_before:
        return True
    return False

def cancel_reservation(trip_object, passenger_id):
    """function to cancel reservation"""
    driver_id = trip_object["driver_id"]
    trip_id = trip_object["trip_id"]
    total_seats = trip_object["total_seats"]
    remaining_seats = trip_object["remaining_seats"]
    driver_preferences = user_data_table.get_item(Key={"user_id": driver_id})["Item"]
    passenger_object = users_table.get_item(Key={"user_id": passenger_id})["Item"]
    #step1: remove passenger reservation from passengers list on trip object
    for item in trip_object["passengers"]:
        if item[0] == passenger_id:
            reservation_id = item[1]
            trip_object["passengers"].remove(item)
    try:
        #step2: remove reservation from trip sessions
        trip_session = trips_sessions_table.get_item(Key={"trip_id": trip_id})["Item"]
        trip_session["reservations"].remove(reservation_id)
        trips_sessions_table.put_item(Item=trip_session)
        #step3: remove reservation from user reservations
        user_reservations = user_reservations_table.get_item(Key={"user_id": passenger_id})["Item"]
        user_reservations["reservations"].remove(reservation_id)
        user_reservations_table.put_item(Item=user_reservations)
        #step4: update trip object with the new number of seats and removing the passenger
        reservation_object = trips_reservations_table.get_item(
            Key={"reservation_id": reservation_id})["Item"]
        updated_seats = get_updated_seats(int(total_seats), int(remaining_seats),
                                          int(reservation_object["reservated_seats"]))
        trip_object["reservated_seats"] = updated_seats["reservated_seats"]
        trip_object["remaining_seats"] = updated_seats["remaining_seats"]
        trip_object["available"] = updated_seats["available"]
        trips_table.put_item(Item=trip_object)
        #step5: remove reservation from trip reservations
        trips_reservations_table.delete_item(Key={"reservation_id": reservation_id})
        #step6: notify the driver
        if driver_preferences["push"] is True:
            send_push_notification(passenger_object, driver_preferences,
                                       "Reserva cancelada", "ha cancelado la reserva")
        #step7: handle chat. Check if there is any other trip with the driver.
        dynamodb.update_item(
            TableName=CHAT_TABLE,
            Key={'chat_id': reservation_object['chat_id']},
            UpdateExpression='SET #attr = :val',
            ExpressionAttributeNames={'#attr': 'is_available'},
            ExpressionAttributeValues={':val': {'BOOL': False}})
        return success_return_parser(f"Trip {trip_id} has been canceled successfully",
                                     None)
    except ClientError as error:
        return error_return_parser(
            error.response["Error"]["Message"], error.response["Error"]["Code"])
    except (ValueError, IndexError):
        return error_return_parser("invalid trip", None)

def cancel_trip(trip_object):
    """function to cancel trip"""
    reservations_list = []
    requests_list = []
    trip_id = trip_object["trip_id"]
    driver_id = trip_object["driver_id"]
    driver_object = users_table.get_item(Key={"user_id": driver_id})["Item"]
    try:
        #step1: change status of trip
        trips_table.update_item(Key={"trip_id": trip_id},
                    UpdateExpression="SET #attr1 = :val1, #attr2 = :val2",
                    ExpressionAttributeNames={"#attr1": "status","#attr2": "available"},
                    ExpressionAttributeValues={":val1": "canceled", ":val2": False})
        #step2: get (if any) all the reservation requests
        for request in trip_object["pending_requests"]:
            requests_list.append({"reservation_id": {"S": request}})
        if len(requests_list) > 0:
            trip_requests = dynamodb.batch_get_item(RequestItems={
                TRIPS_RESERVATIONS_TABLE:{"Keys":requests_list}})["Responses"]["trips_reservations"]
            for request in trip_requests:
                passenger_requests = user_requests_table.get_item(Key={
                    "user_id":request["user_id"]["S"]})["Item"]
                passenger_preferences = user_data_table.get_item(Key = {
                    "user_id":request["user_id"]["S"]})["Item"]
                passenger_requests["requests"].remove(request["reservation_id"]["S"])
                user_requests_table.put_item(Item=passenger_requests)
                trips_reservations_table.delete_item(Key={
                    "reservation_id": request["reservation_id"]["S"]})
                if passenger_preferences["push"] is True:
                    send_push_notification(driver_object, passenger_preferences,
                                       "Viaje cancelado", "ha cancelado el viaje")
        #step3: get trip session to cancel the current reservations
        trips_sessions = trips_sessions_table.get_item(Key={"trip_id": trip_id})["Item"]
        trips_sessions_table.delete_item(Key={"trip_id": trip_id})
        #step4: get all the reservations objects
        for item in trips_sessions["reservations"]:
            reservations_list.append({"reservation_id": {"S": item}})
        if len(reservations_list) == 0:
            return success_return_parser(f"Trip {trip_id} has been canceled successfully", None)
        trip_reservations = dynamodb.batch_get_item(RequestItems={
            TRIPS_RESERVATIONS_TABLE:{"Keys":reservations_list}})["Responses"]["trips_reservations"]
        for reservation in trip_reservations:
            passenger_reservations = user_reservations_table.get_item(Key={
                "user_id":reservation["user_id"]["S"]})["Item"]
            passenger_preferences = user_data_table.get_item(Key = {
                "user_id":reservation["user_id"]["S"]})["Item"]
            passenger_reservations["reservations"].remove(reservation["reservation_id"]["S"])
            user_reservations_table.update_item(
                Key={"user_id": reservation["user_id"]["S"]},
                UpdateExpression="SET reservations = :val",
                ExpressionAttributeValues={":val": passenger_reservations["reservations"]})
            trips_reservations_table.delete_item(Key={
                "reservation_id": reservation["reservation_id"]["S"]})
            #handle the chat
            chat_table.update_item(Key={
                "chat_id": reservation['chat_id']['S']},
                UpdateExpression='SET #attr = :val',
                ExpressionAttributeNames={'#attr': 'is_available'},
                ExpressionAttributeValues={':val': False})
            if passenger_preferences["push"] is True:
                send_push_notification(driver_object, passenger_preferences,
                                       "Viaje cancelado", "ha cancelado el viaje")
        return success_return_parser(f"Trip {trip_id} has been canceled successfully", None)
    except ClientError as error:
        return error_return_parser(
            error.response["Error"]["Message"], error.response["Error"]["Code"])
    except ValueError:
        return error_return_parser("invalid trip", None)

def lambda_handler(event, context):
    """lambda handler"""
    user_id = event["body-json"]["userId"]
    trip_id = event["body-json"]["tripId"]
    trip_object = trips_table.get_item(Key={"trip_id": trip_id})["Item"]
    if check_time(trip_object["departure_time"]) is False:
        return error_return_parser("Unable to cancel the trip", "InvalidCancelationTime")
    if user_id == trip_object["driver_id"]:
        return cancel_trip(trip_object)
    return cancel_reservation(trip_object, user_id)
