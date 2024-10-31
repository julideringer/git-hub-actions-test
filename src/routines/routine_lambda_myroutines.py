"""function to retrieve routines"""
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from src.common_tools.payload_parser import success_return_parser, error_return_parser

ROUTINES_TABLE = "routines"

routines_table = boto3.resource("dynamodb").Table(ROUTINES_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    user_id = event['params']['querystring']['userId']
    try:
        routines = routines_table.query(IndexName='driver_id-index',
                                    KeyConditionExpression=Key('driver_id').eq(user_id))['Items']
        return success_return_parser(None, routines)
    except ClientError as error:
        return error_return_parser(
            error.response['Error']['Message'],error.response['Error']['Code'])
