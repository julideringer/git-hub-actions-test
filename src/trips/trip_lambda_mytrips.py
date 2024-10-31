"""lambda function to retrieve assgined trips to user"""
from copy import deepcopy
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from src.common_tools.payload_parser import error_return_parser, success_return_parser
from src.trips_tools.parser_tools import response_trip_parser
from src.trips_tools.get_user_info import get_user_info_from_objectb64, get_user_info_from_tripsb64

USER_TABLE = "users"
USER_RESERVATIONS_TABLE = "user_reservations"
USER_REQUESTS_TABLE = "user_requests"
TRIPS_TABLE = "trips"
TRIPS_RESERVATIONS_TABLE = "trips_reservations"

users_table = boto3.resource("dynamodb").Table(USER_TABLE)
trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
trips_reservations_table = boto3.resource("dynamodb").Table(TRIPS_RESERVATIONS_TABLE)
user_reservations_table = boto3.resource("dynamodb").Table(USER_RESERVATIONS_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USER_REQUESTS_TABLE)
dynamodb = boto3.client("dynamodb")

def split_list(lst, sublist_size):
    """function to split lists in sublist"""
    return [lst[i:i+sublist_size] for i in range(0, len(lst), sublist_size)]

def get_reservation_requests(trip_id):
    """function to get reservation request for a given trip"""
    reservation_requests = trips_reservations_table.query(
            IndexName="trip_id-index",
            KeyConditionExpression=Key("trip_id").eq(trip_id),
            FilterExpression=Attr("status").eq("pending"))["Items"]
    for request in reservation_requests:
        user_info = users_table.get_item(Key = {"user_id": request["user_id"]})["Item"]
        request["user_info"] = get_user_info_from_objectb64(user_info)
    return reservation_requests

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
        if trip["pending_requests"]:
            trip["requests_info"] = get_reservation_requests(trip["trip_id"])
        if trip["passengers"]:
            trip["passengers_info"] = get_passengers_info(trip["passengers"])
        parsed_trips.append(deepcopy(response_trip_parser(trip)))
    trips = sorted(parsed_trips, key=lambda x: x["departure_time"], reverse=False)[:15]
    return trips

def get_reserved_trips(user_id):
    """function to get reserved trips by user"""
    reservation_list = []
    trips = []

    reservations = user_reservations_table.get_item(Key={"user_id": user_id})["Item"]
    requests = user_requests_table.get_item(Key={"user_id": user_id})["Item"]

    for reservation in reservations["reservations"]:
        reservation_list.append({"reservation_id": {"S": reservation}})
    for request in requests["requests"]:
        reservation_list.append({"reservation_id": {"S": request}})
    if len(reservation_list) == 0:
        return reservation_list

    reservation_response = dynamodb.batch_get_item(RequestItems={
        TRIPS_RESERVATIONS_TABLE:{"Keys": reservation_list}})["Responses"]["trips_reservations"]
    reservation_list.clear()

    unique_trip_ids = [{"trip_id": reservation["trip_id"]} for reservation in reservation_response]
    for trip_id in unique_trip_ids:
        if trip_id not in reservation_list:
            reservation_list.append(trip_id)

    reserved_trips = dynamodb.batch_get_item(RequestItems={
        TRIPS_TABLE: {"Keys": reservation_list}})["Responses"]["trips"]
    reserved_trips = [{k: v[list(v.keys())[0]] for k, v in item.items()} \
                                    for item in reserved_trips]
    reserved_trips = sorted(reserved_trips, key=lambda x: x["departure_time"], reverse=False)[:15]
    for trip in reserved_trips:
        trips.append(deepcopy(response_trip_parser(trip)))
        for reservation in reservation_response:
            if trip["trip_id"] == reservation["trip_id"]["S"]:
                trip["reservation_status"] = reservation["status"]["S"]
    trips = get_user_info_from_tripsb64(trips)
    return trips

def lambda_handler(event, context = None):
    """lambda function in charge of retrieve the trips related to a given user"""
    user_id = event["params"]["querystring"]["userId"]
    try:
        published_trips = get_published_trips(user_id)
        reserved_trips = get_reserved_trips(user_id)
        return success_return_parser(
            None, {"reservedTrips": reserved_trips, "publishedTrips": published_trips})
    except ClientError as error:
        return error_return_parser(
             error.response["Error"]["Message"], error.response["Error"]["Code"])
