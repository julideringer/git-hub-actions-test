"""lambda function to refuse trip request"""
import json
import time
import boto3
from botocore.exceptions import ClientError
from common_tools.send_notifications import send_push_notification
from common_tools.payload_parser import success_return_parser, error_return_parser

TRIPS_RESERVATIONS = "trips_reservations"
TRIPS_REQUESTS = "trips_requests"
USERS_TABLE = "users"
USER_DATA_TABLE = "user_data"
USER_REQUESTS_TABLE = "user_requests"
TRIPS_TABLE = "trips"
CHATS_TABLE = "chat"

chat_table = boto3.resource("dynamodb").Table(CHATS_TABLE)
trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
trips_requests_table = boto3.resource("dynamodb").Table(TRIPS_REQUESTS)
users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USER_REQUESTS_TABLE)

lambda_client = boto3.client("lambda")

def notify_user(request_object):
    """function to notify passenger"""
    #TODO: review notifications
    passenger_preferences = user_data_table.get_item(
        Key={"user_id": request_object["passenger_id"]})["Item"]
    driver_object = users_table.get_item(Key={"user_id": request_object["driver_id"]})["Item"]
    if passenger_preferences["push"] is True:
        send_push_notification(
            driver_object, passenger_preferences,
            "Solicitud rechazada", "ha rechazado tu reserva", request_object["chat_id"])
    message = {"body": json.dumps({
        "action": "reservationRefuse", "receiver": request_object["passenger_id"],
        "sender": request_object["driver_id"],
        "message": "user has refused your reservation request",
        "reservation_id": request_object["request_id"],
        "trip": request_object["trip_id"], "type": "text", 
        "timestamp": f"{int(time.time())}", "chat_id": request_object["chat_id"]})}
    return message

def lambda_handler(event, context):
    """lambda handler"""
    request_id = event["params"]["path"]["id"]
    try:
        #STEP 1. set request to false
        request_object = trips_requests_table.get_item(Key={"request_id": request_id})["Item"]
        request_object["confirmed"] = False
        request_object["status"] = "refused"
        trips_requests_table.put_item(Item=request_object)

        #STEP 2. update user requests table
        user_requests = user_requests_table.get_item(
            Key={"user_id": request_object["passenger_id"]})["Item"]
        user_requests["requests"].remove(request_object["request_id"])
        user_requests_table.put_item(Item=user_requests)

        #STEP 3. update trip object
        trip_object = trips_table.get_item(Key={"trip_id": request_object["trip_id"]})["Item"]
        trip_object["requests"].remove(request_object["request_id"])
        trips_table.put_item(Item=trip_object)

        #STEP 4. update chat object
        chat_object = chat_table.get_item(Key={"chat_id": request_object["chat_id"]})["Item"]
        chat_object["requests"].remove(request_object["request_id"])
        chat_table.put_item(Item=chat_object)

        #STEP 5. notify passenger
        message = notify_user(request_object)
        lambda_client.invoke(FunctionName="ws-send_message", InvocationType="Event",
                             Payload=json.dumps(message))
        return success_return_parser(f"Reservation request {request_object['request_id']} \
                                     has been refused successfully", None)
    except ClientError as error:
        return error_return_parser(
            error.response["Error"]["Message"], error.response["Error"]["Code"])
