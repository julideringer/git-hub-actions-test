"""lambda function to add vehicle to user"""
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

VEHICLES_TABLE = "vehicles"

vehicles_table = boto3.resource("dynamodb").Table(VEHICLES_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    user_id = event["params"]["path"]["id"]
    vehicle_id = event["params"]["path"]["vid"]
    try:
        item = {
            "vehicle_id": vehicle_id,
            "brand": event["body-json"]["brand"],
            "model": event["body-json"]["model"],
            "plate": event["body-json"]["plate"],
            "colour": event["body-json"]["colour"],
            "user_id": user_id
        }
        vehicles_table.put_item(Item=item)
        return success_return_parser("vehicle has been updated properly",
                                     None)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
 