"""lambda function to retrieve assgined trips to user"""
from copy import deepcopy
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from common_tools.payload_parser import error_return_parser, success_return_parser
from common_tools.payload_parser import dict_parser_to_camel_case
from trips_tools.parser_tools import response_trip_parser
from common_tools.get_user_info import get_user_info

USER_TABLE = "users"
TRIPS_TABLE = "trips"
TRIPS_RESERVATIONS_TABLE = "trips_reservations"
TRIPS_REQUESTS_TABLE = "trips_requests"

users_table = boto3.resource("dynamodb").Table(USER_TABLE)
trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
trips_reservations_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS_TABLE)
dynamodb = boto3.client("dynamodb")

def get_passengers_info(passengers):
    """function to get passengers for a given trip"""
    user_list = []
    user_info_list = []
    reservation_list = []
    for passenger in passengers:
        user_info_list.append({"user_id": {"S": passenger[0]}})
        reservation_list.append({"reservation_id": {"S": passenger[1]}})
    user_info = dynamodb.batch_get_item(RequestItems={
        USER_TABLE:{"Keys": user_info_list}})["Responses"]["users"]
    reservations_info = dynamodb.batch_get_item(RequestItems={
        TRIPS_RESERVATIONS_TABLE:{"Keys": reservation_list}})["Responses"]["trips_reservations"]
    user_info = [{k: v[list(v.keys())[0]] for k, v in item.items()} \
                                for item in user_info]
    reservations_info = [{k: v[list(v.keys())[0]] for k, v in item.items()} \
                                for item in reservations_info]
    for reservation in reservations_info:
        for user in user_info:
            if reservation["user_id"] == user["user_id"]:
                user_object = get_user_info_from_objectb64(user)
                user_object["chat_id"] = reservation["chat_id"]
                user_list.append(user_object)
    return user_list

def get_reservations_requests(requests):
    """function to get reservation request for a given trip"""
    request_list = []
    passengers_list = []
    response = []
    for request in requests:
        request_list.append({"request_id": {"S": request}})
    request_objects = dynamodb.batch_get_item(RequestItems={
        TRIPS_REQUESTS_TABLE:{"Keys": request_list}})["Responses"]["trips_requests"]
    for request in request_objects:
        passengers_list.append({"user_id": request["passenger_id"]})
    passengers = dynamodb.batch_get_item(RequestItems={
        USER_TABLE: {"Keys": passengers_list}})["Responses"]["users"]
    passengers = [{k: v[list(v.keys())[0]] for k, v in item.items()} for item in passengers]
    requests = [{k: v[list(v.keys())[0]] for k, v in item.items()} for item in request_objects]
    passengers_info = [get_user_info(passenger) for passenger in passengers]
    for request in requests:
        for passenger in passengers_info:
            if request["passenger_id"] == passenger["user_id"]:
                response.append({"requestId": request["request_id"],
                                 "userInfo": dict_parser_to_camel_case(passenger)})
    return response

def get_reservations_completed(reservations):
    """function to get reservation request for a given trip"""
    reservations_list = []
    passengers_list = []
    response = []
    for reservation in reservations:
        reservations_list.append({"reservation_id": {"S": reservation}})
    reservation_objects = dynamodb.batch_get_item(RequestItems={
        TRIPS_RESERVATIONS_TABLE:{"Keys": reservations_list}})["Responses"]["trips_reservations"]
    for reservation in reservation_objects:
        passengers_list.append({"user_id": reservation["passenger_id"]})
    passengers = dynamodb.batch_get_item(RequestItems={
        USER_TABLE: {"Keys": passengers_list}})["Responses"]["users"]
    passengers = [{k: v[list(v.keys())[0]] for k, v in item.items()} for item in passengers]
    reservations = [{k: v[list(v.keys())[0]] for k, v in item.items()} for item in reservation_objects]
    passengers_info = [get_user_info(passenger) for passenger in passengers]
    for reservation in reservations:
        for passenger in passengers_info:
            if reservation["passenger_id"] == passenger["user_id"]:
                response.append({"reservationId": reservation["reservation_id"],
                                 "userInfo": dict_parser_to_camel_case(passenger)})
    return response

def get_published_trips(user_id):
    """function to get published trips by user"""
    current_timestamp = str(datetime.now().replace(microsecond=0).isoformat())
    parsed_trips = []
    trips = trips_table.query(
            IndexName="driver_id-departure_time-index",
            KeyConditionExpression=Key("driver_id").eq(user_id)\
                &Key("departure_time").gt(current_timestamp),
            FilterExpression=Attr("status").ne("canceled"),
            ScanIndexForward=False,)["Items"]
    for trip in trips:
        if trip["requests"]:
            trip["requests_info"] = get_reservations_requests(trip["requests"])
        if trip["reservations"]:
            trip["passengers_info"] = get_reservations_completed(trip["reservations"])
        parsed_trips.append(deepcopy(dict_parser_to_camel_case(response_trip_parser(trip))))
    trips = sorted(parsed_trips, key=lambda x: x["departureTime"], reverse=False)[:15]
    return trips

def lambda_handler(event, context = None):
    """lambda function in charge of retrieve the trips related to a given user"""
    user_id = event["params"]["querystring"]["userId"]
    try:
        published_trips = get_published_trips(user_id)
        return success_return_parser(None, published_trips)
    except ClientError as error:
        return error_return_parser(
             error.response["Error"]["Message"], error.response["Error"]["Code"])
