"""function to confirm reservation"""
import json
import uuid
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from src.common_tools.payload_parser import success_return_parser, error_return_parser
from src.trips_tools.get_user_info import get_user_info_from_objectb64
from src.trips_tools.messaging_tools import send_push_notification, message_parser
from src.trips_tools.seats_tools import required_seats_function

TRIPS_TABLE = "trips"
USERS_TABLE = "users"
USER_DATA_TABLE = "user_data"
USER_RESERVATIONS_TABLE = "user_reservations"
USER_REQUESTS_TABLE = "user_requests"
USER_CHATS_TABLE = "user_chats"
CHAT_TABLE = "chat"
TRIPS_RESERVATIONS_TABLE = "trips_reservations"
TRIPS_SESSIONS_TABLE = "trips_sessions"

lambda_client = boto3.client("lambda")
dynamodb = boto3.client("dynamodb")
eventbridge = boto3.client("events")

trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USER_REQUESTS_TABLE)
chat_table = boto3.resource("dynamodb").Table(CHAT_TABLE)
trips_reservations_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS_TABLE)
trips_sessions_table = boto3.resource("dynamodb").Table(TRIPS_SESSIONS_TABLE)

def create_eventbridge_rule(alarm_time, trip_id, label, rule_names):
    """Convertir alarm_time a cron expression"""
    cron_expression = alarm_time.strftime("cron(%M %H %d %m ? %Y)")
    rule_name = f"Notify_{label}_trip_{trip_id}"
    if rule_name in rule_names:
        return
    eventbridge.put_rule(
        Name=rule_name,
        ScheduleExpression=cron_expression,
        State="ENABLED",
    )
    eventbridge.put_targets(
                Rule=rule_name,
                Targets=[{
                    "Id": label,
                    "Arn": "arn:aws:lambda:eu-west-1:416737519422:function:lambda_send_alarm_queue",
                    "Input": json.dumps({
                        "trip_id": trip_id,
                        "time_frame": label.replace("Notify", "").replace("Before", " antes")
                    })
                }]
            )
    lambda_client.add_permission(
        FunctionName="arn:aws:lambda:eu-west-1:416737519422:function:lambda_send_alarm_queue",
        StatementId=f"AllowEventBridge_{rule_name}",
        Action="lambda:InvokeFunction",
        Principal="events.amazonaws.com",
        SourceArn=f"arn:aws:events:eu-west-1:416737519422:rule/{rule_name}"
    )

def set_trip_alarms(departure_time, trip_id):
    """function to set trip alarms"""
    departure_time = datetime.strptime(departure_time, "%Y-%m-%dT%H:%M:%S")
    timezone_offset = timedelta(hours=-2)# Ajuste para UTC-2
    adjusted_departure_time = departure_time + timezone_offset
    alarm_times = {
        "N4H": adjusted_departure_time - timedelta(hours=4),
        "N2H": adjusted_departure_time - timedelta(hours=2),
        "N30M": adjusted_departure_time - timedelta(minutes=30),
    }
    response = eventbridge.list_rules()
    rules = response.get("Rules", [])
    rule_names = [rule["Name"] for rule in rules]

    for label, alarm_time in alarm_times.items():
        create_eventbridge_rule(alarm_time, trip_id, label, rule_names)

def automatic_reservation(reservation_object, trip_object):
    """funciton to set automatic reservation"""
    passenger_id = reservation_object["user_id"]
    driver_id = reservation_object["driver_id"]
    chat_id = reservation_object["chat_id"]
    driver_preferences = user_data_table.get_item(Key={"user_id": driver_id})["Item"]
    passenger_object = users_table.get_item(Key={"user_id": passenger_id})["Item"]
    passenger_user_info = get_user_info_from_objectb64(passenger_object)
    trips_reservations_table.put_item(Item=reservation_object)
    if driver_preferences["push"] is True:
        send_push_notification(passenger_object, driver_preferences,
                               "Nueva reserva para tu viaje", "se ha unido a tu viaje", chat_id)
    message = message_parser(passenger_id, driver_id, chat_id,
                             f"{passenger_id} has reserved the trip",
                             trip_object, passenger_user_info)
    return message

def manual_reservation(reservation_object, trip_object):
    """function to set manual reservation"""
    driver_id = reservation_object["driver_id"]
    passenger_id = reservation_object["user_id"]
    chat_id = reservation_object["chat_id"]
    user_requests = user_requests_table.get_item(Key={"user_id": passenger_id})["Item"]["requests"]
    user_requests.remove(reservation_object["reservation_id"])
    user_requests_table.put_item(Item={"user_id": passenger_id, "requests": user_requests})
    passenger_preferences = user_data_table.get_item(Key={"user_id": passenger_id})["Item"]
    driver_object = users_table.get_item(Key = {"user_id": driver_id})["Item"]
    driver_user_info = get_user_info_from_objectb64(driver_object)
    trips_reservations_table.put_item(Item=reservation_object)        
    if passenger_preferences["push"] is True:
        send_push_notification(driver_object, passenger_preferences,
                     "Reserva confirmada", "ha aceptado tu solicitud", chat_id)
    message = message_parser(driver_id, passenger_id, chat_id,
                             f"{driver_id} has confirmed your request",
                             trip_object, driver_user_info)
    return message

def lambda_handler(event, context):
    """lambda handler"""
    user_id = event["body-json"]["userId"]
    trip_id = event["body-json"]["tripId"]
    required_seats = event["body-json"]["requiredSeats"]
    trip_object = trips_table.get_item(Key = {"trip_id": trip_id})["Item"]
    if trip_object is None:
        return error_return_parser("invalid trip", None)
    updated_seats = required_seats_function(int(required_seats),
                                            int(trip_object["remaining_seats"]),
                                            int(trip_object["reservated_seats"]))
    if updated_seats["success"] is False:
        return updated_seats
    if event["body-json"]["reservationMode"] == "manual":
        reservation_id = event["body-json"]["reservationId"]
        chat_id = event["body-json"]["chatId"]
        reservation_object = {
            "reservation_id": reservation_id, "trip_id": trip_id,
            "driver_id": trip_object["driver_id"],
            "user_id": user_id, "reservated_seats": required_seats, "chat_id": chat_id,
            "confirmed": True, "status": "accepted"}
        message = manual_reservation(reservation_object, trip_object)
    elif event["body-json"]["reservationMode"] == "auto":
        chat_id = str(uuid.uuid4())
        reservation_id = str(uuid.uuid4())
        reservation_object = {
            "reservation_id": reservation_id, "trip_id": trip_id,
            "driver_id": trip_object["driver_id"], "user_id": user_id,
            "reservated_seats": required_seats, "chat_id": chat_id, 
            "confirmed": True, "status": "accepted"}
        message = automatic_reservation(reservation_object, trip_object)
    else:
        return error_return_parser( "invalid payload", None)
    try:
        for i in range (0, int(required_seats)):
            trip_object["passengers"].append([user_id, reservation_id])
        trip_object["reservated_seats"] = updated_seats["data"][1][":val1"]
        trip_object["remaining_seats"] = updated_seats["data"][1][":val2"]
        trip_object["available_seats"] = updated_seats["data"][1][":val3"]
        trips_table.put_item(Item = trip_object)
        chat_table.put_item(Item = {
            "chat_id": chat_id, "driver_id": trip_object["driver_id"], "user_id": user_id,
            "reservation_id": reservation_id, "trip_id": trip_id, "is_available": True,
            "status": "confirmed"})
        dynamodb.update_item(
            TableName=USER_RESERVATIONS_TABLE,
            Key = {"user_id": {"S": user_id}},
            UpdateExpression="SET reservations = list_append(reservations, :val1)",
            ExpressionAttributeValues={":val1": {"L": [{"S": reservation_id}]}},
            ReturnValues="UPDATED_NEW")
        dynamodb.update_item(
            TableName=USER_CHATS_TABLE,
            Key = {"user_id": {"S": user_id}},
            UpdateExpression="SET chat_sessions = list_append(chat_sessions, :val1)",
            ExpressionAttributeValues={":val1": {"L": [{"S": chat_id}]}},
            ReturnValues="UPDATED_NEW")
        dynamodb.update_item(
            TableName=USER_CHATS_TABLE,
            Key = {"user_id": {"S": trip_object["driver_id"]}},
            UpdateExpression="SET chat_sessions = list_append(chat_sessions, :val1)",
            ExpressionAttributeValues=
            {":val1": {"L": [{"S": chat_id}]}},
            ReturnValues="UPDATED_NEW")
        dynamodb.update_item(
            TableName=TRIPS_SESSIONS_TABLE,
            Key = {"trip_id": {"S": trip_object["trip_id"]}},
            UpdateExpression="SET reservations = list_append(reservations, :i)",
            ExpressionAttributeValues={":i": {"L": [{"S": reservation_id}]},},
            ReturnValues="UPDATED_NEW")
        set_trip_alarms(trip_object["departure_time"], trip_id)
        lambda_client.invoke(FunctionName="ws-send_message", InvocationType="Event",
                             Payload=message)
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
    return success_return_parser("seats booked correctly", {"chat_id": chat_id, "trip_id": trip_id})
