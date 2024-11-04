"""lambda function for manual reservation"""
import os
import uuid
import json
import boto3
from botocore.exceptions import ClientError
import stripe
from common_tools.payload_parser import error_return_parser, success_return_parser
from common_tools.send_notifications import message_parser, send_push_notification
from common_tools.get_user_info import get_user_info_from_objectb64
from trips_tools.seats_tools import required_seats_function

stripe.api_key = os.environ["stripe_api_key"]
reservation_secret = os.environ["reservation_wh_secret"]

USERS_TABLE = "users"
USER_DATA_TABLE = "user_data"
USER_REQUESTS_TABLE = "user_requests"
USER_RESERVATIONS_TABLE = "user_reservations"
TRIPS_TABLE = "trips"
TRIPS_REQUESTS_TABLE = "trips_requests"
TRIPS_RESERVATIONS_TABLE = "trips_reservations"
CHAT_TABLE = "chat"
USER_CHATS_TABLE = "user_chats"

lambda_client = boto3.client("lambda")
dynamodb = boto3.client("dynamodb")

users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USER_REQUESTS_TABLE)
user_chats_table = boto3.resource("dynamodb").Table(USER_CHATS_TABLE)
trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
trip_reservations_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS_TABLE)
trip_requests_table = boto3.resource("dynamodb").Table(TRIPS_REQUESTS_TABLE)
chat_table = boto3.resource("dynamodb").Table(CHAT_TABLE)

def send_chat_message(action, chat_id, sender, receiver, content, trip_object):
    """function to send chat message"""
    passenger_object = users_table.get_item(Key={"user_id": sender})["Item"]
    passenger_user_info = get_user_info_from_objectb64(passenger_object)
    message = message_parser(action, sender, receiver, chat_id, content,
                             trip_object, passenger_user_info)
    lambda_client.invoke(FunctionName="ws-send_message",
                         InvocationType="Event", Payload=json.dumps(message))

def send_notification(sender, receiver, title, body):
    """send notification"""
    #TODO: review notifications
    passenger_object = users_table.get_item(Key={"user_id": sender})["Item"]
    receiver_preferences = user_data_table.get_item(Key={"user_id": receiver})["Item"]
    passenger_user_info = get_user_info_from_objectb64(passenger_object)
    if receiver_preferences["push"] is True:
        send_push_notification(passenger_user_info, receiver_preferences, title, body)

def update_chat(chat_id, reservation_object, reservation_mode):
    """function to create the chat"""
    if reservation_mode == "manual":
        update_expression = "SET requests = list_append(requests, :val1)"
    elif reservation_mode == "auto":
        update_expression = "SET reservations = list_append(reservations, :val1)"
    else:
        raise ClientError
    expression_attribute_values = {":val1": {"L": [{"S": reservation_object["reservation_id"]}]}}
    dynamodb.update_item(
        TableName=CHAT_TABLE,
        Key = {"chat_id": {"S": chat_id}},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="UPDATED_NEW")

def create_chat(reservation_object, reservation_mode):
    """function to create the chat"""
    chat_object = {
        "chat_id": str(uuid.uuid4()), "is_available": True,
        "requests": [], "reservations": [],
        "user1": reservation_object["driver_id"], "user2": reservation_object["passenger_id"]
    }
    if reservation_mode == "manual":
        chat_object["reservations"] = []
        chat_object["requests"].append(reservation_object["reservation_id"])
    if reservation_mode == "auto":
        chat_object["reservations"].append(reservation_object["reservation_id"])
        chat_object["requests"] = []
    chat_table.put_item(Item=chat_object)
    dynamodb.update_item(
        TableName=USER_CHATS_TABLE,
        Key = {"user_id": {"S": reservation_object["passenger_id"]}},
        UpdateExpression="SET chat_sessions = list_append(chat_sessions, :val1)",
        ExpressionAttributeValues={":val1": {"L": [{"S": chat_object["chat_id"]}]}},
        ReturnValues="UPDATED_NEW")
    dynamodb.update_item(
        TableName=USER_CHATS_TABLE,
        Key = {"user_id": {"S": reservation_object["driver_id"]}},
        UpdateExpression="SET chat_sessions = list_append(chat_sessions, :val1)",
        ExpressionAttributeValues={":val1": {"L": [{"S": chat_object["chat_id"]}]}},
        ReturnValues="UPDATED_NEW")
    return chat_object

def get_chat_id(reservation_object, reservation_mode):
    """function to create the reserve"""
    driver_chats = user_chats_table.get_item(Key={
        "user_id": reservation_object["driver_id"]})["Item"]["chat_sessions"]
    user_chats = user_chats_table.get_item(Key={
        "user_id": reservation_object["passenger_id"]})["Item"]["chat_sessions"]
    common_chats = list(set(driver_chats)&set(user_chats))
    if common_chats:
        chat_object = chat_table.get_item(Key={"chat_id": common_chats[0]})["Item"]
        update_chat(chat_object["chat_id"], reservation_object, reservation_mode)
        return chat_object["chat_id"]
    chat_object = create_chat(reservation_object, reservation_mode)
    return chat_object["chat_id"]

def manual_reservation(trip_object, reservation_object):
    """manual reservation handler"""
    passenger_id = reservation_object["passenger_id"]
    reservation_object["request_id"] = reservation_object["reservation_id"]
    del reservation_object["reservation_id"]
    reservation_object["confirmed"] = False
    reservation_object["status"] = "pending"
    trip_requests_table.put_item(Item=reservation_object)
    trip_object["requests"].append(reservation_object["request_id"])
    trips_table.put_item(Item=trip_object)
    user_requests = user_requests_table.get_item(Key={"user_id": passenger_id})["Item"]["requests"]
    user_requests.append(reservation_object["request_id"])
    user_requests_table.put_item(Item={"user_id": passenger_id, "requests": user_requests})

def auto_reservation(trip_object, reservation_object):
    """auto reservation handler"""
    passenger_id = reservation_object["passenger_id"]
    reservation_id = reservation_object["reservation_id"]
    reservation_object["confirmed"] = True
    reservation_object["status"] = "accepted"
    trip_reservations_table.put_item(Item=reservation_object)
    for _ in range (0, int(reservation_object["reservated_seats"])):
        trip_object["reservations"].append(reservation_id)
    trips_table.put_item(Item=trip_object)
    dynamodb.update_item(
        TableName=USER_RESERVATIONS_TABLE,
        Key = {"user_id": {"S": passenger_id}},
        UpdateExpression="SET reservations = list_append(reservations, :val)",
        ExpressionAttributeValues={":val": {"L": [{"S": reservation_id}]}},
        ReturnValues="UPDATED_NEW")

def lambda_handler(event, context):
    """lambda handler"""
    payload = event["body-json"]
    if payload["type"] == "payment_intent.payment_failed":
        print("❌ Payment failed.")
        return error_return_parser("❌ Payment failed.", None)
    if payload["type"] == "payment_intent.succeeded":
        passenger_id = payload["data"]["object"]["metadata"]["userId"]
        trip_id = payload["data"]["object"]["metadata"]["tripId"]
        required_seats = payload["data"]["object"]["metadata"]["requiredSeats"]
        payment_id = payload["data"]["object"]["id"]
        print("💰 Payment received!")
    else:
        return error_return_parser("Unhandled event received", None)
    try:
        trip_object = trips_table.get_item(Key = {"trip_id": trip_id})["Item"]
        updated_seats = required_seats_function(
            int(required_seats),
            int(trip_object["remaining_seats"]),
            int(trip_object["reservated_seats"]))
        if updated_seats["success"] is False:
            return updated_seats
        reservation_object = {
            "reservation_id": str(uuid.uuid4()), "trip_id": trip_id, "payment_id": payment_id,
            "reservated_seats": required_seats, "passenger_id": passenger_id,
            "driver_id": trip_object["driver_id"]
        }
        print(reservation_object["driver_id"])
        driver_chats_usss= user_chats_table.get_item(Key={
        "user_id": '9a4aabde-32f5-40d6-9a7c-9ea2d85c3432'})
        reservation_object["chat_id"] = get_chat_id(reservation_object,
                                                    trip_object["reservation_mode"])
        if trip_object["reservation_mode"] == "manual":
            manual_reservation(trip_object, reservation_object)
            action, body = "reservationRequest", "New trip request"
            send_notification(passenger_id, reservation_object["driver_id"],
                              "Solicitud de reserva", "body")
        elif trip_object["reservation_mode"] == "auto":
            trip_object["reservated_seats"] = updated_seats["data"][1][":val1"]
            trip_object["remaining_seats"] = updated_seats["data"][1][":val2"]
            auto_reservation(trip_object, reservation_object)
            action, body = "reservationConfirmation", "New trip reservation"
            send_notification(passenger_id, reservation_object["driver_id"],
                              "Nueva reserva para tu viaje", "se ha unido a tu viaje")
        else:
            return error_return_parser("unable to do the reservation", "invalidReservationMode")
        send_chat_message(
                action, reservation_object["chat_id"], passenger_id,
                reservation_object["driver_id"], body, trip_object)
        if trip_object["reservation_mode"] == "manual":
            return success_return_parser("seats requested correctly",
                                     {"chatId": reservation_object["chat_id"],
                                      "requestId": reservation_object["request_id"]})
        return success_return_parser("seats booked correctly",
                                     {"chatId": reservation_object["chat_id"],
                                      "reservationId": reservation_object["reservation_id"]})
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])

#TODO: when reservation fails, remove the reservation object.
#TODO: averiguate what is available seats (BOOL)
