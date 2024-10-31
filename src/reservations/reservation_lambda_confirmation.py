"""function to confirm reservation"""
import copy
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser
from common_tools.get_user_info import get_user_info_from_objectb64
from common_tools.send_notifications import send_push_notification, message_parser
from trips_tools.seats_tools import required_seats_function

TRIPS_TABLE = "trips"
USERS_TABLE = "users"
USER_DATA_TABLE = "user_data"
USER_RESERVATIONS_TABLE = "user_reservations"
TRIPS_RESERVATIONS_TABLE = "trips_reservations"
USER_REQUESTS_TABLE = "user_requests"
TRIPS_REQUESTS_TABLE = "trips_requests"
CHAT_TABLE = "chat"

lambda_client = boto3.client("lambda")
dynamodb = boto3.client("dynamodb")

trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)
user_reservations_table = boto3.resource("dynamodb").Table(USER_RESERVATIONS_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USER_REQUESTS_TABLE)
trips_reservations_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS_TABLE)
trips_requests_table = boto3.resource("dynamodb").Table(TRIPS_REQUESTS_TABLE)
chat_table = boto3.resource("dynamodb").Table(CHAT_TABLE)

def notify_passenger(passenger_id, driver_object, chat_id, trip_object):
    """function to notify the user"""
    #TODO: review notifications
    passenger_preferences = user_data_table.get_item(Key={"user_id": passenger_id})["Item"]
    driver_user_info = get_user_info_from_objectb64(driver_object)
    if passenger_preferences["push"] is True:
        send_push_notification(driver_object, passenger_preferences,
                    "Reserva confirmada", "ha aceptado tu solicitud", chat_id)
    message = message_parser(driver_object["driver_id"], passenger_id, chat_id,
                            f"{driver_object['driver_id']} has confirmed your request",
                            trip_object, driver_user_info)
    lambda_client.invoke(FunctionName="ws-send_message", InvocationType="Event",
                        Payload=message)

def manual_reservation(request_object, reservation_object, trip_object):
    """function to set manual reservation"""
    passenger_id = reservation_object["passenger_id"]
    reservation_id = reservation_object["reservation_id"]
    trips_reservations_table.put_item(Item=reservation_object)
    trips_requests_table.delete_item(Key={"request_id": request_object["request_id"]})
    user_requests = user_requests_table.get_item(Key={"user_id": passenger_id})["Item"]["requests"]
    user_requests.remove(reservation_id)
    user_requests_table.put_item(Item={"user_id": passenger_id, "requests": user_requests})
    user_reservations = user_reservations_table.get_item(
        Key={"user_id": passenger_id})["Item"]["reservations"]
    user_reservations.append(reservation_id)
    user_reservations_table.put_item(Item={"user_id":passenger_id,"reservations":user_reservations})
    trip_object["requests"].remove(reservation_id)
    trips_table.put_item(Item=trip_object)
    chat_object = chat_table.get_item(Key={reservation_object["chat_id"]})
    chat_object["requests"].remove(request_object["request_id"])
    chat_object["reservations"].append(request_object["request_id"])
    chat_table.put_item(Item=chat_object)

def lambda_handler(event, context):
    """lambda handler"""
    request_id = event["params"]["path"]["id"]
    request_object = trips_requests_table.get_item(Key={"request_id": request_id})["Item"]
    reservation_object = copy.deepcopy(request_object)
    trip_id = request_object["trip_id"]
    required_seats = request_object["reservated_seats"]
    trip_object = trips_table.get_item(Key = {"trip_id": trip_id})["Item"]
    if trip_object is None:
        return error_return_parser("invalid trip", None)
    updated_seats = required_seats_function(int(required_seats),
                                            int(trip_object["remaining_seats"]),
                                            int(trip_object["reservated_seats"]))
    if updated_seats["success"] is False:
        return updated_seats
    reservation_object["status"] = "accepted"
    reservation_object["confirmed"] = True
    reservation_object["reservation_id"] = reservation_object["request_id"]
    del reservation_object["request_id"]
    trip_object["reservated_seats"] = updated_seats["data"][1][":val1"]
    trip_object["remaining_seats"] = updated_seats["data"][1][":val2"]
    trip_object["available_seats"] = updated_seats["data"][1][":val3"]
    for _ in range (int(required_seats)):
        trip_object["reservations"].append(request_id)
    try:
        manual_reservation(request_object, reservation_object, trip_object)
        #STEP4: notify passenger
        #STEP5: send message to passenger
        return success_return_parser("seats booked correctly",
                                     {"chat_id": reservation_object["chat_id"],
                                      "trip_id": trip_id})
    except ClientError as error:
        error_update_expression = "SET reservated_seats = :val1,\
                                    remaining_seats = :val2,\
                                    trips_available = :val3"
        error_attribute_values = {
            ":val1": trip_object["reservated_seats"],
            ":val2": trip_object["remaining_seats"],
            ":val3": str(True)
        }
        trips_table.update_item(Key={"trip_id": trip_id},
                        ConditionExpression= Attr("trip_id").eq(trip_id),
                        UpdateExpression=error_update_expression,
                        ExpressionAttributeValues=error_attribute_values)
        return error_return_parser(
            error.response["Error"]["Message"], error.response["Error"]["Code"])
