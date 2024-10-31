"""lambda function to retrive available chats"""
from copy import deepcopy
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser
from common_tools.payload_parser import dict_parser_to_camel_case
from common_tools.get_user_info import get_user_info
from trips_tools.parser_tools import response_trip_parser

USER_CHATS_TABLE = "user_chats"
USERS_TABLE = "users"
CHAT_TABLE = "chat"
TRIPS_TABLE = "trips"
RESERVATIONS_TABLE = "trips_reservations"
REQUESTS_TABLE = "trips_requests"

dynamodb = boto3.client("dynamodb")
user_chats_table = boto3.resource("dynamodb").Table(USER_CHATS_TABLE)
users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
chat_table = boto3.resource("dynamodb").Table(CHAT_TABLE)
trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)

def get_trips(reservations, requests):
    """function to get trips from reservations and requests"""
    reservations_list = []
    requests_list = []
    trips_list = []
    trips_response = []
    for reservation in reservations:
        reservations_list.append({"reservation_id": reservation})
    for request in requests:
        requests_list.append({"request_id": request})
    reservations.clear()
    requests.clear()
    if len(reservations_list) > 0:
        reservations = dynamodb.batch_get_item(RequestItems={
            RESERVATIONS_TABLE: {"Keys": reservations_list}
        })["Responses"]["trips_reservations"]
    if len(requests_list) > 0:
        requests = dynamodb.batch_get_item(RequestItems={
            REQUESTS_TABLE: {"Keys": requests_list}
        })["Responses"]["trips_requests"]
    for request in requests:
        trips_list.append({"trip_id": request["trip_id"]})
    for reservation in reservations:
        trips_list.append({"trip_id": reservation["trip_id"]})
    trips = dynamodb.batch_get_item(RequestItems={
        TRIPS_TABLE: {"Keys": trips_list}
    })["Responses"]["trips"]
    trips = [{k: v[list(v.keys())[0]] for k, v in item.items()} for item in trips]
    for trip in trips:
        trips_response.append(deepcopy(dict_parser_to_camel_case(response_trip_parser(trip))))
    return trips_response

def get_available_chats(user_id):
    """retrieve available chats"""
    available_chats_list = []

    #STEP 1: get active chats for a given user
    available_chats = user_chats_table.get_item(Key = {"user_id": user_id})["Item"]["chat_sessions"]
    if len(available_chats) == 0:
        return available_chats

    #STEP 2: get chat objects
    for chat in available_chats:
        available_chats_list.append({"chat_id": {"S": chat}})
    return dynamodb.batch_get_item(RequestItems={
        CHAT_TABLE: {"Keys": available_chats_list}})["Responses"]["chat"]

def lambda_handler(event, context):
    """lambda handler"""
    user_id = event["params"]["querystring"]["userId"]
    response = []
    try:
        #STEP 1: get available chats
        chat_response = get_available_chats(user_id)
        for item in chat_response:
            if item["user1"]["S"] != user_id:
                user_object = users_table.get_item(Key={"user_id": item["user1"]["S"]})["Item"]
                user_info = dict_parser_to_camel_case(get_user_info(user_object))
            elif item["user2"]["S"] != user_id:
                user_object = users_table.get_item(Key={"user_id": item["user2"]["S"]})["Item"]
                user_info = dict_parser_to_camel_case(get_user_info(user_object))
            else:
                return error_return_parser("Invalid User", None)
            trips = get_trips(item["reservations"]["L"], item["requests"]["L"])
            response.append({
                "chatId": item["chat_id"]["S"],
                "userInfo": user_info,
                "commonTrips": trips})
        return success_return_parser("", response)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
