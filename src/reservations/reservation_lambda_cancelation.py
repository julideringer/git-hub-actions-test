"""lambda funtion to cancel trips"""
import json
import time
from datetime import datetime
from datetime import timedelta
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser
from common_tools.send_notifications import send_push_notification
from trips_tools.seats_tools import get_updated_seats

USERS_TABLE = "users"
USER_DATA_TABLE = "user_data"
USER_RESERVATIONS_TABLE = "user_reservations"
TRIPS_RESERVATIONS_TABLE = "trips_reservations"
TRIPS_TABLE = "trips"
CHAT_TABLE = "chat"

trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)
user_reservations_table = boto3.resource("dynamodb").Table(USER_RESERVATIONS_TABLE)
trips_reservations_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS_TABLE)
chat_table = boto3.resource("dynamodb").Table(CHAT_TABLE)

def notify_user(reservation_object):
    """function to notify passenger"""
    #TODO: review notifications
    driver_preferences = user_data_table.get_item(
        Key={"user_id": reservation_object["driver_id"]})["Item"]
    passenger_object = users_table.get_item(Key={"user_id": reservation_object["passenger_id"]})["Item"]
    if driver_preferences["push"] is True:
        send_push_notification(passenger_object, driver_preferences,
                               "Reserva cancelada", "ha cancelado la reserva")
    message = {"body": json.dumps({
        "action": "reservationRefuse", "receiver": reservation_object["passenger_id"],
        "sender": reservation_object["driver_id"],
        "message": "user has refused your reservation request",
        "reservation_id": reservation_object["reservation_id"],
        "trip": reservation_object["trip_id"], "type": "text", 
        "timestamp": f"{int(time.time())}", "chat_id": reservation_object["chat_id"]})}
    return message

def check_time(departure_time):
    """function to check if request fits cancelation policy"""
    current_time = datetime.now().isoformat(timespec="seconds")
    current_time_obj = datetime.strptime(current_time, "%Y-%m-%dT%H:%M:%S")
    departure_time_obj = datetime.strptime(departure_time, "%Y-%m-%dT%H:%M:%S")
    one_hour_before = departure_time_obj - timedelta(hours=1)
    if current_time_obj <= one_hour_before:
        return True
    return False

def lambda_handler(event, context):
    """lambda handler"""
    reservation_id = event["params"]["path"]["id"]
    try:
        reservation_object = trips_reservations_table.get_item(
            Key={"reservation_id": reservation_id})["Item"]
        trip_object = trips_table.get_item(
            Key={"trip_id": reservation_object["trip_id"]})["Item"]
        if check_time(trip_object["departure_time"]) is False:
            return error_return_parser("Unable to cancel the trip", "InvalidCancelationTime")

        #STEP 1: cancel reservation object
        reservation_object["confirmed"] = False
        reservation_object["status"] = "canceled"
        trips_reservations_table.put_item(Item=reservation_object)

        #STEP 2: remove reservation from user reservations
        user_reservations = user_reservations_table.get_item(
            Key={"user_id": reservation_object["passenger_id"]})["Item"]
        user_reservations["reservations"].remove(reservation_object["reservation_id"])
        user_reservations_table.put_item(Item=user_reservations)

        #STEP3: remove reservations from trip_object
        for reservation in trip_object["reservations"]:
            if reservation == reservation_object["reservation_id"]:
                trip_object["reservations"].remove(reservation)
        updated_seats = get_updated_seats(int(trip_object["reservated_seats"]),
                                          int(trip_object["remaining_seats"]),
                                          int(reservation_object["reservated_seats"]))
        trip_object["remaining_seats"] = updated_seats["remaining_seats"]
        trip_object["reservated_seats"] = updated_seats["reservated_seats"]
        trip_object["available"] = updated_seats["available"]
        trips_table.put_item(Item=trip_object)

        #STEP 4. remove reservations from chat
        chat_object = chat_table.get_item(Key={"chat_id": reservation_object["chat_id"]})["Item"]
        chat_object["reservations"].remove(reservation_object["reservation_id"])
        chat_table.put_item(Item=chat_object)

        #STEP 5: notify the driver
        notify_user(reservation_object)
        return success_return_parser("Reservation has been canceled successfully", None)
        #TODO: Refund trip amount

    except ClientError as error:
        return error_return_parser(
            error.response["Error"]["Message"], error.response["Error"]["Code"])
    except (ValueError, IndexError):
        return error_return_parser("invalid trip", None)
