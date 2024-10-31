"""lambda function to send batchs of creation trips to SQS"""
import json
import uuid
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from src.routines_tools.routine_functions import parse_sqs_batch_item_format, \
    split_list, parser_to_dynamodb_case_routines

ROUTINES_TABLE = 'routines'

dynamodb = boto3.client('dynamodb')
queue_object = boto3.client('sqs')
TRIPS_QUEUE_URL = 'https://sqs.eu-west-1.amazonaws.com/416737519422/trips_q'

def lambda_handler(event, context):
    """lambda handler"""
    for record in event['Records']:
        routine = json.loads(record["body"])
        routine['routine_id'] = str(uuid.uuid4())
        routine_object = parser_to_dynamodb_case_routines(routine)
        routine_object['creation_date'] = {"S":str(datetime.now().isoformat(timespec='seconds'))}
        routine_object['departure_time'] = {"L":[{"S": time} for time in routine['departure_time']]}
        try:
            dynamodb.put_item(TableName=ROUTINES_TABLE, Item=routine_object)
            batch_buffer = []
            departure_time_list = routine.get('departure_time')
            items_buffer = [routine] * len(departure_time_list)
            batch_buffer = [parse_sqs_batch_item_format(item, departure_time_list.pop(0)) for item in items_buffer]
            batch_buffer = split_list(batch_buffer, 10)
            for element in batch_buffer:
                queue_object.send_message_batch(QueueUrl = TRIPS_QUEUE_URL,
                                                Entries = element)
        except ClientError as error:
            print({
                "success": False, 
                "message": error.response['Error']['Message'],
                "code": error.response['Error']['Code']
            })
            return False
    return True
