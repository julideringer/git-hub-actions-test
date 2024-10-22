"""Lambda function publish Trips"""
import uuid
from datetime import datetime
import boto3
import geohash
from botocore.exceptions import ClientError

TRIPS_TABLE = 'trips'
TRIPS_SESSIONS = 'trips_sessions'

trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)
trips_sessions_table = boto3.resource("dynamodb").Table(TRIPS_SESSIONS)

def parser_to_camel_case(raw_item):
    """lambda function to parse to camel case"""
    return {
        'driver_id': raw_item['userId'],
        'vehicle_id': raw_item['vehicleId'],
        'departure_location': raw_item['departureLocation'],
        'arrival_location': raw_item['arrivalLocation'],
        'latitude_departure': raw_item['latitudDeparture'],
        'longitude_departure': raw_item['longitudDeparture'],
        'latitude_arrival': raw_item['latitudArrival'],
        'longitude_arrival': raw_item['longitudArrival'],
        'departure_time': raw_item['departureTime'],
        'arrival_time': raw_item['arrivalTime'],
        'total_seats': raw_item['totalSeats'],
        'comment': raw_item['comment'],
        'price': raw_item['price'],
        'reservation_mode': raw_item['reservationMode'],
    }

def lambda_handler(event, context= None):
    """lambda handler"""
    body = parser_to_camel_case(event['body-json'])
    trip_id = str(uuid.uuid4())
    body['trip_id'] = trip_id
    body['geohash_departure'] = geohash.encode(float(body['latitude_departure']),
                                       float(body['longitude_departure']), 5)
    body['geohash_arrival'] = geohash.encode(float(body['latitude_arrival']),
                                     float(body['longitude_arrival']), 5)
    body['status'] = 'pending'
    body['reservated_seats'] = '0'
    body['remaining_seats'] = body['total_seats']
    body['available'] = True
    body['creation_date'] = str(datetime.now().isoformat(timespec='seconds'))
    try:
        trips_table.put_item(Item = body)
        trips_sessions_table.put_item(Item={'trip_id': trip_id, 'reservations': []})
        response = {"success": True, "data":
                {"message": f'Trip {trip_id} has been published successfully',"info": None}}
    except ClientError as error:
        response = {"success": False,"error_message": error.response['Error']['Message'],
                "error_code": error.response['Error']['Code'],"data": None}
    return response
