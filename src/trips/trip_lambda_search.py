"""lambda function for trip reservation"""
from datetime import datetime, timedelta
from copy import deepcopy
import geohash
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from trips_tools.parser_tools import response_trip_parser
from common_tools.get_user_info import get_user_info_from_tripsb64
from common_tools.payload_parser import error_return_parser, success_return_parser
from common_tools.payload_parser import dict_parser_to_camel_case

trips_table = boto3.resource("dynamodb").Table("trips")

def lambda_handler(event, context = None):
    """lambda_handler"""
    parsed_trips = []
    encoded_departure = geohash.encode(float(event["body-json"]["latitudDeparture"]),
                                              float(event["body-json"]["longitudDeparture"]),5)
    encoded_arrival = geohash.encode(float(event["body-json"]["latitudArrival"]),
                                            float(event["body-json"]["longitudArrival"]),5)
    neigbours_coincidences_departure = geohash.neighbors(encoded_departure)
    neigbours_coincidences_departure.append(encoded_departure)
    neigbours_coincidences_arrival = geohash.neighbors(encoded_arrival)
    neigbours_coincidences_arrival.append(encoded_arrival)
    date_obj = datetime.fromisoformat(event["body-json"]["departureTime"])
    time_before = str(date_obj - timedelta(hours=2)).replace(" ", "T")
    time_later = str(date_obj + timedelta(hours=2)).replace(" ", "T")

    search_query = (Attr("driver_id").ne(event["body-json"]["userId"]) \
        & Attr("geohash_departure").is_in(neigbours_coincidences_departure) \
        & Attr("geohash_arrival").is_in(neigbours_coincidences_arrival) \
        & Attr("departure_time").between(time_before,time_later) \
        & (Attr("remaining_seats").eq(str(event["body-json"]["passengers"])) \
        | Attr("remaining_seats").gt(str(event["body-json"]["passengers"]))) \
        & Attr("available").eq(True))

    try:
        query_results = trips_table.scan(FilterExpression=search_query)["Items"]
        if len(query_results) == 0:
            return success_return_parser("no trip available", None)
        trips =  get_user_info_from_tripsb64(query_results)
        for trip in trips:
            parsed_object = dict_parser_to_camel_case(response_trip_parser(trip))
            parsed_trips.append(deepcopy(parsed_object))
        return success_return_parser(None, parsed_trips)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
