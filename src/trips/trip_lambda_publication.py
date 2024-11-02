"""Lambda function publish Trips"""
import uuid
from datetime import datetime
import boto3
import geohash
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser
from trips_tools.parser_tools import parser_to_snake_case

TRIPS_TABLE = "trips"

trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)

def lambda_handler(event, context= None):
    """lambda handler"""
    body = parser_to_snake_case(event["body-json"])
    trip_id = str(uuid.uuid4())
    body["trip_id"] = trip_id
    body["geohash_departure"] = geohash.encode(float(body["latitude_departure"]),
                                       float(body["longitude_departure"]), 5)
    body["geohash_arrival"] = geohash.encode(float(body["latitude_arrival"]),
                                     float(body["longitude_arrival"]), 5)
    body["status"] = "pending"
    body["reservated_seats"] = "0"
    body["remaining_seats"] = body["total_seats"]
    body["available"] = True
    body["creation_date"] = str(datetime.now().isoformat(timespec="seconds"))
    body["requests"] = []
    body["reservations"] = []
    try:
        trips_table.put_item(Item = body)
        return success_return_parser(f"Trip {trip_id} has been published successfully", None)
    except ClientError as error:
        return error_return_parser(
            error.response["Error"]["Message"], error.response["Error"]["Code"])
