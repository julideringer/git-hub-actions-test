"""function to retrieve routines"""
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

ROUTINES_TABLE = "routines"

routines_table = boto3.resource("dynamodb").Table(ROUTINES_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    print("holaaaaljljljsdfdfaa")
    user_id = event['params']['querystring']['userId']
    try:
        routines = routines_table.query(IndexName='driver_id-index',
                                    KeyConditionExpression=Key('driver_id').eq(user_id))['Items']
        return {"success": True, "data": routines, "info": None}
    except ClientError as error:
        return {
            "success": False, "error_message": error.response['Error']['Message'],
            "error_code": error.response['Error']['Code'], "data": None}
