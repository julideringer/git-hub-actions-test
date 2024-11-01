"""lambda function to add vehicle to user"""
import uuid
import boto3
from botocore.exceptions import ClientError
from common_tools.payload_parser import success_return_parser, error_return_parser

VEHICLES_TABLE = "vehicles"

vehicles_table = boto3.resource("dynamodb").Table(VEHICLES_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    print("holatest")
    user_id = event["params"]["path"]["id"]
    vehicle_id = str(uuid.uuid4())
    try:
        vehicles_table.put_item(
            Item={
                "vehicle_id": vehicle_id,
                "user_id": user_id,
                "brand": event["body-json"]["brand"],
                "model": event["body-json"]["model"],
                "plate": event["body-json"]["plate"],
                "colour": event["body-json"]["colour"],
            })
        return success_return_parser("vehicle has been registered properly", None)
    except ClientError as error:
        if error.operation_name == "UpdateItem":
            vehicles_table.delete_item(Key={"vehicle_id": vehicle_id})
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
