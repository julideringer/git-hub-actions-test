"""lambda function to publish routines"""
import json
import boto3
import geohash
from botocore.exceptions import ClientError
from src.routines_tools.routine_functions import parser_to_camel_case
from src.common_tools.payload_parser import success_return_parser, error_return_parser

queue_object = boto3.client("sqs")
ROUTINES_QUEUE_URL = 'https://sqs.eu-west-1.amazonaws.com/416737519422/routines_q'

def lambda_handler(event, context = None):
    """lambda handler"""
    body = parser_to_camel_case(event.get('body-json'))
    body['geohash_departure'] = geohash.encode(float(body['latitude_departure']),
                                       float(body['longitude_departure']), 5)
    body['geohash_arrival'] = geohash.encode(float(body['latitude_arrival']),
                                     float(body['longitude_arrival']), 5)
    body['remaining_seats'] = body['total_seats']
    body['reservated_seats'] = str(0)
    body['driver_id'] = body['user_id']
    del body['user_id']
    try:
        queue_object.send_message(
            QueueUrl = ROUTINES_QUEUE_URL,
            MessageBody = json.dumps(body),
            DelaySeconds = 1
        )
    except ClientError as error:
        return error_return_parser(error.response['Error']['Message'],
                                   error.response['Error']['Code'])
    return success_return_parser("Routine has been created successfully", None)
