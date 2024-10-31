"""lambda function for trip reservation"""
from datetime import datetime
from copy import deepcopy
import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

USERS = "users"
TRIPS = "trips"
TRIPS_ARCHIVE = "trips_archive"
TRIPS_SESSIONS = "trips_sessions"
TRIPS_SESSIONS_ARCHIVE = "trips_sessions_archive"
TRIPS_RESERVATIONS = "trips_reservations"
TRIPS_RESERVATIONS_ARCHIVE = "trips_reservations_archive"
CHATS = "chat"
CHATS_ARCHIVE = "chat_archive"
MESSSAGES = "messages"
MESSSAGES_ARCHIVE = "messages_archive"

dynamodb_client = boto3.client("dynamodb")
trips_table = boto3.resource("dynamodb").Table(TRIPS)
trips_archive_table = boto3.resource("dynamodb").Table(TRIPS_ARCHIVE)
trips_reservations_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS)
trips_reservations_archive = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS_ARCHIVE)
trips_sessions_table = boto3.resource("dynamodb").Table(TRIPS_SESSIONS)
trips_sessions_archive = boto3.resource("dynamodb").Table(TRIPS_SESSIONS_ARCHIVE)
chat_table = boto3.resource("dynamodb").Table(CHATS)
chat_archive_table = boto3.resource("dynamodb").Table(CHATS_ARCHIVE)
messages_table = boto3.resource("dynamodb").Table(MESSSAGES)
messages_archive_table = boto3.resource("dynamodb").Table(MESSSAGES_ARCHIVE)
users_table = boto3.resource("dynamodb").Table(USERS)

def migrate_elements(items, key_id, destination_table, source_table, db_format = None):
    """function to move trips to archive table"""
    if len(items) == 0:
        return False
    if db_format:
        with destination_table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
        for item in items:
            source_table.delete_item(Key={key_id: item[key_id]})
    else:
        items_aux = []
        for item in items:
            items_aux.append({'PutRequest': {'Item': deepcopy(item)}})
        dynamodb_client.batch_write_item(RequestItems={destination_table: items_aux})
        for item in items:
            source_table.delete_item(Key={key_id: item[key_id]["S"]})
    return True

def get_session_list(trip_list):
    """function to retrieve older sessions"""
    return trips_sessions_table.scan(
        FilterExpression=Attr('trip_id').is_in(trip_list)
    )["Items"]

def get_reservation_list(trip_list):
    """function to retrieve older reservations"""
    return trips_reservations_table.scan(
        FilterExpression=Attr('trip_id').is_in(trip_list)
    )["Items"]

def get_chat_list(trip_list):
    """function to retrieve older chats"""
    return chat_table.scan(
        FilterExpression=Attr('trip_id').is_in(trip_list)
    )["Items"]

def get_users_list(chat_list):
    """function to update user info"""
    users_list = []
    for item in chat_list:
        if {"user_id": item["user_id"]} not in users_list:
            users_list.append({"user_id": item["user_id"]})
        if {"user_id": item["driver_id"]} not in users_list:
            users_list.append({"user_id": item["driver_id"]})
    return users_list

def get_messages_list(chat_list):
    "function to retrieve older messages from chats"
    messages_list = []
    for chat in chat_list:
        messages_list.append(messages_table.query(
        IndexName = 'chat_id-timestamp-index',
        KeyConditionExpression=Key('chat_id').eq(chat["chat_id"]["S"]))['Items'])
    return messages_list

def remove_users_chat(users_list, chat_list, sessions_list):
    """disattach older chats from users"""
    users_reponse = dynamodb_client.batch_get_item(
        RequestItems={USERS: {"Keys": users_list}})["Responses"]["users"]
    for user in users_reponse:
        chat_session_list = deepcopy(user["chat_sessions"]["L"])
        reservations_list = deepcopy(user["reservations"]["L"])
        for chat_session in chat_session_list:
            if {"chat_id": chat_session} in chat_list:
                user["chat_sessions"]["L"].remove(chat_session)
        for reservation in reservations_list:
            if {"reservation_id": reservation} in sessions_list:
                user["reservations"]["L"].remove(reservation)
    users_response_aux = []
    for item in users_reponse:
        users_response_aux.append({'PutRequest': {'Item': deepcopy(item)}})
    dynamodb_client.batch_write_item(RequestItems={USERS: users_response_aux})

def lambda_handler(event=None, context=None):
    """lambda handler"""
    current_timestamp = str(datetime.now().replace(microsecond=0).isoformat())
    try:
        trip_list = trips_table.scan(
            FilterExpression="departure_time < :dep_time",
            ExpressionAttributeValues={":dep_time": current_timestamp})['Items']
        if len(trip_list) == 0:
            return {"success": True, "data": {
                "message": "Nothing to migrate", "info": None}}
        sessions_list = get_session_list(trip_list)
        reservations_list = get_reservation_list(trip_list)
        chats_list = get_chat_list(trip_list)
        users_list = get_users_list(chats_list)
        messages_list = get_messages_list(chats_list)
        if len(users_list) != 0:
            remove_users_chat(users_list, chats_list, sessions_list)
        #migrar mensajes
        for messages_chat in messages_list:
            migrate_elements(messages_chat, 'message_id', messages_archive_table, messages_table,
                             True)
        #migrar chats from chat table
        migrate_elements(chats_list, 'chat_id', CHATS_ARCHIVE, chat_table)
        #borrar reservations from users table
        migrate_elements(reservations_list, 'reservation_id', TRIPS_RESERVATIONS_ARCHIVE,
                         trips_reservations_table)
        #migrar trip_sessions
        migrate_elements(sessions_list, 'trip_id', TRIPS_SESSIONS_ARCHIVE,
                         trips_sessions_table)
        #migrar trips
        migrate_elements(trip_list, 'trip_id', trips_archive_table, trips_table, True)
        return {"success": True, "data": {
                "message": "Migration done succesfully", "info": None}}
    except ClientError as error:
        return {
            "success": False, "message": error.response['Error']['Message'],
            "code": error.response['Error']['Code'], "data": None}
