"""lambda function to store the new trips in database"""
import json
import copy
from datetime import datetime
import boto3

TRIPS_TABLE = 'trips'
SESSIONS_TABLE = 'trips_sessions'

trips_table = boto3.resource('dynamodb').Table(TRIPS_TABLE)
sessions_table = boto3.resource('dynamodb').Table(SESSIONS_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    buffer = []
    sessions_buffer = []
    for record in event["Records"]:
        msg = json.loads(record['body'])
        msg['creation_date'] = str(datetime.now().isoformat(timespec='seconds'))
        msg['price'] = str(msg['price'])
        buffer.append(copy.deepcopy(msg))
        sessions_buffer.append(copy.deepcopy({'trip_id': msg['trip_id'], 'reservations': []}))
    with trips_table.batch_writer() as batch:
        for item in buffer:
            batch.put_item(Item=item)
    with sessions_table.batch_writer() as batch:
        for item in sessions_buffer:
            batch.put_item(Item=item)
    return True
