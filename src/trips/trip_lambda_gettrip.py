"""lambda function to get trip by Id"""
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser
from common_tools.payload_parser import dict_parser_to_camel_case
from trips_tools.parser_tools import response_trip_parser

TRIP_TABLE = "trips"

trip_table = boto3.resource("dynamodb").Table(TRIP_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    trip_id = event["params"]["querystring"]["id"]
    try:
        trip_object = trip_table.get_item(Key={"trip_id": trip_id})["Item"]
        parsed_object = dict_parser_to_camel_case(
            response_trip_parser(trip_object))
        return success_return_parser("", parsed_object)
    except ClientError as error:
        return error_return_parser(
            error.response["Error"]["Message"], error.response["Error"]["Code"])
