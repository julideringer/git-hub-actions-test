"""lambda function to delete vehicle"""
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import error_return_parser, success_return_parser

VEHICLES_TABLE = "vehicles"

vehicles_table = boto3.resource("dynamodb").Table(VEHICLES_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    vehicle_id = event["params"]["path"]["vid"]
    try:
        vehicles_table.delete_item(Key={"vehicle_id": vehicle_id})
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
    except ValueError:
        return error_return_parser("invalid vehicle", None)
    return success_return_parser("vehicle has been deleted properly", None)
