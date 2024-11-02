"""lambda function for trip reservation"""
from datetime import datetime
from copy import deepcopy
from geopy.distance import geodesic
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
from trips_tools.parser_tools import response_trip_parser
from common_tools.get_user_info import get_user_info_from_trips
from common_tools.payload_parser import error_return_parser, success_return_parser
from common_tools.payload_parser import dict_parser_to_camel_case

trips_table = boto3.resource("dynamodb").Table("trips")

def add_distance(items, latitud_ref, longitud_ref, distancia):
    """add distance item"""
    cercanos=[]
    item_no_distance=[]
    for item in items:
        lat_punto = float(item["latitude_departure"])
        lon_punto = float(item["longitude_departure"])
        coord_punto = (lat_punto, lon_punto)
        distancia_item = geodesic((latitud_ref, longitud_ref), coord_punto).kilometers
        item["distancia"] = distancia_item
    items.sort(key=lambda x: x["distancia"])
    for item in items:
        if item["distancia"] <= distancia:
            cercanos.append(item)
        else:
            item_no_distance.append(item)
        if len(cercanos) == 15:
            break
    for item in item_no_distance:
        cercanos.append(item)
        if len(cercanos) == 15:
            break
    return cercanos

def lambda_handler(event, context= None):
    """lambda handler"""
    fecha_hora_actual = datetime.now()
    parsed_trips = []
    fecha_hora_formateada = fecha_hora_actual.strftime("%Y-%m-%dT%H:%M:%S")
    user_id = event["body-json"]["userId"]
    distancia = float(event["body-json"]["distance"])
    try:
        items = trips_table.scan(
            FilterExpression=Attr("departure_time").gte(fecha_hora_formateada)\
                & Attr("driver_id").ne(user_id))["Items"]
        items_sorted = sorted(
            items, key=lambda x: x["departure_time"], reverse=False)
        trips_order_distance = add_distance(items_sorted, event["body-json"]["latitudDeparture"],
                                                 event["body-json"]["longitudDeparture"], distancia)
        if len(trips_order_distance) == 0:
            return success_return_parser("No trip found", trips_order_distance)
        trips = get_user_info_from_trips(trips_order_distance)
        for trip in trips:
            parsed_object = dict_parser_to_camel_case(response_trip_parser(trip))
            parsed_trips.append(deepcopy(parsed_object))
        return success_return_parser(
            None, parsed_trips)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
