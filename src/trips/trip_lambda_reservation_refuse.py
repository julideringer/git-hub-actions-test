"""lambda function to refuse trip request"""
import json
import time
import boto3
from botocore.exceptions import ClientError
from src.trips_tools.messaging_tools import send_push_notification
from src.common_tools.payload_parser import success_return_parser, error_return_parser

TRIPS_RESERVATIONS = "trips_reservations"
USERS_TABLE = "users"
USER_DATA_TABLE = "user_data"
USER_REQUESTS_TABLE = "user_requests"
TRIPS_TABLE = "trips"
CHATS_TABLE = "chat"

chat_table = boto3.resource("dynamodb").Table(CHATS_TABLE)
trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
trips_reservations_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS)
users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USER_REQUESTS_TABLE)

lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    """lambda handler"""
    reservation_id = event["body-json"]["reservationId"]
    passenger_id = event["body-json"]["userId"]
    chat_id = event["body-json"]["chatId"]
    trip_id = event["body-json"]["tripId"]
    trip_object = trips_table.get_item(Key={"trip_id": trip_id})["Item"]
    passenger_preferences = user_data_table.get_item(Key = {"user_id": passenger_id})["Item"]
    driver_object = users_table.get_item(Key = {"user_id": trip_object["driver_id"]})["Item"]
    try:
        user_requests = user_requests_table.get_item(
            Key={"user_id": passenger_id})["Item"]["requests"]
        user_requests.remove(reservation_id)
        trip_object["pending_requests"].remove(reservation_id)
        trips_reservations_table.update_item(
            Key={"reservation_id": reservation_id},
            UpdateExpression="SET #attr = :val, #attr2 = :val2",
            ExpressionAttributeNames={"#attr": "confirmed", "#attr2": "status"},
            ExpressionAttributeValues={":val": False, ":val2": "refused"})
        chat_table.update_item(
            Key={"chat_id": chat_id},
            UpdateExpression="SET #attr1 = :val1, #attr2 = :val2",
            ExpressionAttributeNames={"#attr1": "status", "#attr2": "is_available"},
            ExpressionAttributeValues={":val1": "canceled", ":val2": False})
        user_requests_table.put_item(Item={"user_id": passenger_id, "requests": user_requests})
        trips_table.put_item(Item=trip_object)
        message = {"body": json.dumps({
            "action": "reservationRefuse", "receiver": passenger_id,
            "sender": trip_object["driver_id"],
            "message": "user has refused your reservation request",
            "reservation_id": reservation_id, "trip": trip_id, "type": "text", 
            "timestamp": f"{int(time.time())}", "chat_id": chat_id})}
        lambda_client.invoke(FunctionName="ws-send_message", InvocationType="Event",
                             Payload=json.dumps(message))
        if passenger_preferences["push"] is True:
            send_push_notification(driver_object, passenger_preferences,
                                   "Solicitud rechazada", "ha rechazado tu reserva", chat_id)
        return success_return_parser(
            f"Reservation request {reservation_id} has been canceled successfully", None)
    except ClientError as error:
        return error_return_parser(
            error.response["Error"]["Message"], error.response["Error"]["Code"])
