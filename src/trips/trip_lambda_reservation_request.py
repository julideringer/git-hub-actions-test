"""lambda function for manual reservation"""
import uuid
import json
import time
import boto3
from botocore.exceptions import ClientError
from src.common_tools.payload_parser import error_return_parser, success_return_parser
from src.trips_tools.get_user_info import get_user_info_from_objectb64
from src.trips_tools.messaging_tools import send_push_notification
from src.trips_tools.seats_tools import required_seats_function

USERS_TABLE = "users"
USER_DATA_TABLE = "user_data"
USER_REQUESTS_TABLE = "user_requests"
TRIPS_TABLE = "trips"
TRIPS_RESERVATIONS_TABLE = "trips_reservations"
CHAT_TABLE = "chat"

lambda_client = boto3.client("lambda")

users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USER_REQUESTS_TABLE)
trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
trips_reservation_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS_TABLE)
chat_table = boto3.resource("dynamodb").Table(CHAT_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    passenger_id = event["body-json"].get("userId")
    trip_id = event["body-json"].get("tripId")
    required_seats = event["body-json"].get("requiredSeats")
    trip_object = trips_table.get_item(Key = {"trip_id": trip_id}).get("Item")
    if trip_object is None:
        return {
            "success": False, "error_message": "unavailable trip",
            "error_code": None, "data": None
        }
    updated_seats = required_seats_function(int(required_seats),
                                        int(trip_object.get("remaining_seats")),
                                        int(trip_object.get("reservated_seats")))
    if updated_seats.get("success") is False:
        return updated_seats
    chat_id = str(uuid.uuid4())
    reservation_id = str(uuid.uuid4())
    reservation_object = {
        "reservation_id": reservation_id, "trip_id": trip_id, "user_id": passenger_id,
        "reservated_seats": required_seats, "chat_id": chat_id, "confirmed": False,
        "status": "pending", "driver_id": trip_object["driver_id"]
    }
    try:
        passenger_object = users_table.get_item(Key={"user_id": passenger_id})["Item"]
        passenger_info = get_user_info_from_objectb64(passenger_object)
        driver_preferences = user_data_table.get_item(
            Key={"user_id": trip_object["driver_id"]})["Item"]
        chat_table.put_item(Item={
            "chat_id": chat_id, "driver_id": trip_object["driver_id"],
            "reservation_id": reservation_id, "trip_id": trip_id, "is_available": True,
            "status": "pending", "user_id": passenger_id})
        trips_reservation_table.put_item(Item=reservation_object)
        user_requests_table.update_item(
            Key={"user_id": passenger_id},
            UpdateExpression="SET #attr = list_append(if_not_exists(#attr, :empty_list), :val)",
            ExpressionAttributeNames={'#attr': 'requests'},
            ExpressionAttributeValues={':empty_list': [], ':val': [reservation_id]},
            ReturnValues="UPDATED_NEW")
        trip_object["pending_requests"].append(reservation_id)
        trips_table.put_item(Item=trip_object)
        message = {"body": json.dumps({
            "action": "reservationRequest", "receiver": trip_object["driver_id"],
            "sender": passenger_id, "reservation_id": reservation_id, "trip": trip_object,
            "message": f"request for {required_seats} seats for the trip {trip_id}",
            "user_info": passenger_info, "type": "text", "timestamp": f"{int(time.time())}",
            "chat_id": chat_id})}
        lambda_client.invoke(FunctionName="ws-send_message", InvocationType="Event",
                                Payload=json.dumps(message))
        if driver_preferences["push"] is True:
            #TODO: send email notification
            send_push_notification(passenger_info, driver_preferences, "Solicitud de viaje",
                               "quiere viajar contigo", chat_id)
        return success_return_parser("seats requested correctly", {"chat_id": chat_id})
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
