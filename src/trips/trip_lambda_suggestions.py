"""lambda function for trip reservation"""
from datetime import datetime
from copy import deepcopy
import geohash
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr
from src.trips_tools.get_user_info import get_user_info_from_tripsb64
from src.trips_tools.parser_tools import response_trip_parser
from src.common_tools.payload_parser import success_return_parser, error_return_parser

trips_table = boto3.resource("dynamodb").Table('trips')

def search_nearby_trips(orig_geohash, items_nearby, departure_ecode_five):
    """search_nearby_trips"""
    cercanos = []
    nuevos_items=[]
    nuevos_items_vecinos=[]
    neigbours_coincidentes_departure = geohash.neighbors(orig_geohash)
    for item in items_nearby:
        destino_latitud = float(item['latitude_departure'])
        destino_longitud = float(item['longitude_departure'])
        dest_geohash = geohash.encode(destino_latitud, destino_longitud, precision=6)
        if orig_geohash == dest_geohash:
            cercanos.append(item)
        else:
            nuevos_items.append(item)
        if len(cercanos) == 15:
            break
    for item in nuevos_items:
        destino_latitud = float(item['latitude_departure'])
        destino_longitud = float(item['longitude_departure'])
        dest_geohash = geohash.encode(destino_latitud, destino_longitud, precision=6)
        if dest_geohash in neigbours_coincidentes_departure:
            cercanos.append(item)
        else:
            nuevos_items_vecinos.append(item)
        if len(cercanos) == 15:
            break
    for item in nuevos_items_vecinos:
        destino_latitud = float(item['latitude_departure'])
        destino_longitud = float(item['longitude_departure'])
        dest_geohash = geohash.encode(destino_latitud, destino_longitud, precision=5)
        if departure_ecode_five == dest_geohash:
            cercanos.append(item)
        else:
            cercanos.append(item)
        if len(cercanos) == 15:
            break
    return cercanos

def lambda_handler(event, context= None):
    """lambda handler"""
    parsed_trips = []
    encoded_departure = geohash.encode(float(
        event['body-json']['latitudDeparture']), float(event['body-json']['longitudDeparture']), 6)
    departure_precision_menor = geohash.encode(
        float(event['body-json']['latitudDeparture']),
        float(event['body-json']['longitudDeparture']), 5)
    fecha_hora_actual = datetime.now()
    fecha_hora_formateada = fecha_hora_actual.strftime('%Y-%m-%dT%H:%M:%S')
    user_id = event['body-json']['userId']
    try:
        items = trips_table.scan(
            FilterExpression=Attr('departure_time').gte(fecha_hora_formateada)\
                & Attr('driver_id').ne(user_id))['Items']
        items_sorted = sorted(items, key=lambda x: x['departure_time'], reverse=False)
        nearby_trips = search_nearby_trips(
            encoded_departure, items_sorted, departure_precision_menor)
        if len(nearby_trips) == 0:
            return success_return_parser(None, {"suggestedTrips": nearby_trips})
        trips = get_user_info_from_tripsb64(nearby_trips)[:10]
        for trip in trips:
            parsed_trips.append(deepcopy(response_trip_parser(trip)))
        return success_return_parser(
            None, {"suggestedTrips": parsed_trips})
    except ClientError as error:
        return error_return_parser(
            error.response['Error']['Message'], error.response['Error']['Code'])
