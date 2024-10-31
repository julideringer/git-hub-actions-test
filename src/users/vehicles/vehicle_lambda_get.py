"""lambda function to retrieve vehicle information"""
from copy import deepcopy
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser
from common_tools.payload_parser import dict_parser_to_camel_case

VEHICLES_TABLE = "vehicles"

vehicles_table = boto3.resource("dynamodb").Table(VEHICLES_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    user_id = event["params"]["path"]["id"]
    response = []
    try:
        query_response = vehicles_table.query(
            IndexName="user_id-index",
            KeyConditionExpression=Key("user_id").eq(user_id))["Items"]
        for vehicle in query_response:
            response.append(deepcopy(dict_parser_to_camel_case(vehicle)))
        return success_return_parser(None, {"vehicles": response})
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
