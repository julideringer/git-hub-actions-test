"""module to list all the messaging tools"""
import json
from time import time
import boto3

queue_object = boto3.client("sqs")
NOTIFICATIONS_Q = "https://sqs.eu-west-1.amazonaws.com/416737519422/notifications_q"

def notification_parser(name, chat_id, title, body, platform):
    """function to create notification object"""
    platform_var = "GCM"
    if platform == "ios":
        platform_var = "APNS"
    return json.dumps({
        platform_var: json.dumps({
            "notification": {
                "body": f"{name} {body}",
                "title": title},
            "data": {"chat_id": chat_id}
        })
    })

def send_push_notification(sender, receiver, message1, message2, chat_id = None):
    """function to send message"""
    queue_object.send_message(
        QueueUrl = NOTIFICATIONS_Q,
        MessageBody = notification_parser(
            sender["name"], chat_id, message1, message2, receiver["platform"]),
        MessageAttributes = {
            "device_token": {
                "DataType": "String",
                "StringValue": receiver["device_token"]
            },
            "platform": {
                "DataType": "String",
                "StringValue": receiver["platform"]
            }
        })

def message_parser(sender, receiver, chat_id, content, trip, user_info):
    """function to create msg object"""
    return json.dumps({
        "body": json.dumps({
            "action": "reservationConfirmation",
            "receiver": receiver,
            "sender": sender,
            "user_info": user_info,
            "message": content, 
            "trip": trip,
            "type": "text",
            "timestamp": f"{int(time())}", "chat_id": chat_id}
        )})

def required_seats_function(required_seats, remaining_seats, reserved_seats):
    """function to determine if there free seats or not"""
    trip_available = True
    if required_seats <= remaining_seats:
        reserved_seats_update = required_seats + reserved_seats
        remaining_seats_update = remaining_seats - required_seats
        if remaining_seats_update == 0:
            trip_available = False
        update_expression = "SET reservated_seats = :val1,\
                                remaining_seats = :val2, available = :val3"
        expression_attribute_values = {
            ":val1": str(reserved_seats_update),
            ":val2": str(remaining_seats_update),
            ":val3": trip_available
        }
        return {"success": True, "data": [update_expression, expression_attribute_values]}
    return {"success": False, "error_message": "unavailable number of required seats", "data": None}
