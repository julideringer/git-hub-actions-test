"""function to retrieve routines"""
from copy import deepcopy
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser
from common_tools.payload_parser import dict_parser_to_camel_case

ROUTINES_TABLE = "routines"

routines_table = boto3.resource("dynamodb").Table(ROUTINES_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    user_id = event["params"]["querystring"]["userId"]
    response_list = []
    try:
        routines = routines_table.query(
            IndexName="driver_id-index",
            KeyConditionExpression=Key("driver_id").eq(user_id))["Items"]
        for routine in routines:
            response_list.append(deepcopy(dict_parser_to_camel_case(routine)))
        return success_return_parser(None, response_list)
    except ClientError as error:
        return error_return_parser(
            error.response["Error"]["Message"],error.response["Error"]["Code"])
