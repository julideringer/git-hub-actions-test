"""lambda funtion to cancel trips"""
from datetime import datetime
from datetime import timedelta
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser
from common_tools.send_notifications import send_push_notification

TRIPS_TABLE = "trips"
USERS_TABLE = "users"
USER_DATA_TABLE = "user_data"
USER_REQUESTS_TABLE = "user_requests"
USER_RESERVATIONS_TABLE = "user_reservations"
TRIPS_RESERVATIONS_TABLE = "trips_reservations"
TRIPS_REQUESTS_TABLE = "trips_requests"
CHAT_TABLE = "chat"

dynamodb = boto3.client("dynamodb")
trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USER_REQUESTS_TABLE)
user_reservations_table = boto3.resource("dynamodb").Table(USER_RESERVATIONS_TABLE)
trips_reservations_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS_TABLE)
trips_requests_table = boto3.resource("dynamodb").Table(TRIPS_REQUESTS_TABLE)
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

def send_notifications(passenger_list, driver_id):
    """function to send notifications"""
    #TODO: review notifications
    driver_object = users_table.get_item(Key={"user_id": driver_id})["Item"]
    passengers_preferences = dynamodb.batch_get_item(
        RequestItems={USER_DATA_TABLE: {"Keys": passenger_list}}
    )["Responses"]["user_data"]
    for passenger_preferences in passengers_preferences:
        if passenger_preferences["push"] is True:
            send_push_notification(driver_object, passenger_preferences,
                               "Viaje cancelado", "ha cancelado el viaje")

def cancel_requests(trip_object):
    """function to cancel trip requests"""
    requests_list = []
    passenger_list = []
    for request in trip_object["requests"]:
        requests_list.append({"request_id": {"S": request}})
    if len(requests_list) > 0:
        trip_requests = dynamodb.batch_get_item(RequestItems={
            TRIPS_REQUESTS_TABLE:{"Keys":requests_list}})["Responses"]["trips_requests"]
        for request in trip_requests:
            passenger_list.append({"user_id": request["passenger_id"]})
            chat_id = request["chat_id"]["S"]
            passenger_requests = user_requests_table.get_item(Key={
                "user_id": request["passenger_id"]["S"]})["Item"]
            passenger_requests["requests"].remove(request["request_id"]["S"])
            user_requests_table.put_item(Item=passenger_requests)
            trips_requests_table.delete_item(Key={"request_id": request["request_id"]["S"]})
            chat_object = chat_table.get_item(Key={"chat_id": chat_id})["Item"]
            chat_object["requests"].remove(request["request_id"]["S"])
            chat_object = chat_table.put_item(Item=chat_object)
    #TODO: handle refund
    return passenger_list

def cancel_reservations(trip_object):
    """function to cancel trip reservations"""
    reservations_list = []
    passenger_list = []
    for reservation_id in trip_object["reservations"]:
        reservations_list.append({"reservation_id": {"S": reservation_id}})
    if len(reservations_list) > 0:
        trip_reservations = dynamodb.batch_get_item(RequestItems={
            TRIPS_RESERVATIONS_TABLE:{"Keys":reservations_list}})["Responses"]["trips_reservations"]
        for reservation in trip_reservations:
            passenger_list.append({"user_id": reservation["passenger_id"]})
            chat_id = reservation["chat_id"]["S"]
            passenger_reservations = user_reservations_table.get_item(Key={
                "user_id":reservation["passenger_id"]["S"]})["Item"]
            passenger_reservations["reservations"].remove(reservation["reservation_id"]["S"])
            user_reservations_table.put_item(Item=passenger_reservations)
            trips_reservations_table.delete_item(Key={
                "reservation_id": reservation["reservation_id"]["S"]})
            chat_object = chat_table.get_item(Key={"chat_id": chat_id})["Item"]
            chat_object["reservations"].remove(reservation["reservation_id"]["S"])
            chat_object = chat_table.put_item(Item=chat_object)
    #TODO: handle refund
    return passenger_list

def cancel_trip(trip_object):
    """function to cancel trip"""
    trip_id = trip_object["trip_id"]
    passenger_list = []
    try:
        #step1: change status of trip
        trips_table.update_item(Key={"trip_id": trip_id},
                    UpdateExpression="SET #attr1 = :val1, #attr2 = :val2",
                    ExpressionAttributeNames={"#attr1": "status","#attr2": "available"},
                    ExpressionAttributeValues={":val1": "canceled", ":val2": False})
        #step2: get (if any) all the reservation requests and remove them
        passenger_list += cancel_requests(trip_object)
        #step3: get the current reservations and remove them
        passenger_list += cancel_reservations(trip_object)
        #step4: notify users
        if len(passenger_list) > 0:
            send_notifications(passenger_list, trip_object["driver_id"])
        return success_return_parser(f"Trip {trip_id} has been canceled successfully", None)
    except ClientError as error:
        return error_return_parser(
            error.response["Error"]["Message"], error.response["Error"]["Code"])
    except ValueError:
        return error_return_parser("invalid trip", None)

def lambda_handler(event, context):
    """lambda handler"""
    trip_id = event["params"]["path"]["id"]
    trip_object = trips_table.get_item(Key={"trip_id": trip_id})["Item"]
    if trip_object["available"] is False:
        return error_return_parser("Trip already canceled", "InvalidTripId")
    if check_time(trip_object["departure_time"]) is False:
        return error_return_parser("Unable to cancel the trip", "InvalidCancelationTime")
    if event["body-json"]["userId"] != trip_object["driver_id"]:
        return error_return_parser("Unable to cancel the trip", "UserPermissionsError")
    return cancel_trip(trip_object)
