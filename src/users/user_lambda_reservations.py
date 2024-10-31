"""lambda function to get user reservations"""
from copy import deepcopy
import boto3
from botocore.exceptions import ClientError
from common_tools.get_user_info import get_user_info_from_tripsb64
from common_tools.payload_parser import success_return_parser, error_return_parser
from common_tools.payload_parser import dict_parser_to_camel_case
from trips_tools.parser_tools import response_trip_parser

USER_RESERVATIONS_TABLE = "user_reservations"
TRIPS_RESERVATIONS_TABLE = "trips_reservations"
USER_REQUESTS_TABLE = "user_requests"
TRIPS_REQUESTS_TABLE = "trips_requests"
TRIPS_TABLE = "trips"

user_reservations_table = boto3.resource("dynamodb").Table(USER_RESERVATIONS_TABLE)
user_requests_table = boto3.resource("dynamodb").Table(USER_REQUESTS_TABLE)
dynamodb = boto3.client("dynamodb")

def get_reserved_trips(user_id):
    """function to get reserved trips by user"""
    reservations_list = []
    trip_id_list = []
    #STEP 1. get reservations from user reservations
    reservations = user_reservations_table.get_item(Key={"user_id": user_id})["Item"]
    for reservation in reservations["reservations"]:
        reservations_list.append({"reservation_id": {"S": reservation}})
    if len(reservations_list) == 0:
        return reservations_list

    #STEP 2. get trips from trips reservations
    reservations_objects = dynamodb.batch_get_item(
        RequestItems={TRIPS_RESERVATIONS_TABLE: {"Keys": reservations_list}}
    )["Responses"]["trips_reservations"]
    unique_trip_ids = [{"trip_id": reservation["trip_id"]} for reservation in reservations_objects]
    for trip_id in unique_trip_ids:
        if trip_id not in trip_id_list:
            trip_id_list.append(trip_id)

    #STEP 3. get trips from trips table
    reserved_trips = dynamodb.batch_get_item(
        RequestItems={TRIPS_TABLE: {"Keys": trip_id_list}}
    )["Responses"]["trips"]

    reserved_trips = [{k: v[list(v.keys())[0]] for k, v in item.items()} \
                                    for item in reserved_trips]

    return sorted(reserved_trips, key=lambda x: x["departure_time"], reverse=False)[:15]

def get_requested_trips(user_id):
    """function to retrieve trips requests"""
    requests_list = []
    trip_id_list = []
    requests = user_requests_table.get_item(Key={"user_id": user_id})["Item"]
    for request in requests["requests"]:
        requests_list.append({"request_id": {"S": request}})
    if len(requests_list) == 0:
        return requests_list

    reservations_objects = dynamodb.batch_get_item(
        RequestItems={TRIPS_RESERVATIONS_TABLE: {"Keys": requests_list}}
    )["Responses"]["trips_reservations"]

    unique_trip_ids = [{"trip_id": reservation["trip_id"]} for reservation in reservations_objects]
    for trip_id in unique_trip_ids:
        if trip_id not in trip_id_list:
            trip_id_list.append(trip_id)

    #STEP 3. get trips from trips table
    reserved_trips = dynamodb.batch_get_item(
        RequestItems={TRIPS_TABLE: {"Keys": trip_id_list}}
    )["Responses"]["trips"]

    reserved_trips = [{k: v[list(v.keys())[0]] for k, v in item.items()} \
                                    for item in reserved_trips]

    return sorted(reserved_trips, key=lambda x: x["departure_time"], reverse=False)[:15]

def lambda_handler(event, context):
    """lambda handler"""
    user_id = event["params"]["querystring"]["userId"]
    response_list = []
    try:
        reserved_trips = get_reserved_trips(user_id)
        requested_trips = get_requested_trips(user_id)
        for trip in reserved_trips:
            response_list.append(deepcopy(response_trip_parser(trip)))
        for trip in requested_trips:
            response_list.append(deepcopy(response_trip_parser(trip)))
        if len(response_list) == 0:
            return success_return_parser(None, response_list)
        trips = deepcopy(get_user_info_from_tripsb64(response_list))
        response_list.clear()
        for trip in trips:
            response_list.append(dict_parser_to_camel_case(trip))
        return success_return_parser(None, {"reservedTrips": response_list})
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
