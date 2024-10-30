"""function to get user info for a given list of users"""
from base64 import b64encode
from copy import deepcopy
import boto3

USERS_TABLE = 'users'

users_table = boto3.resource("dynamodb").Table(USERS_TABLE)
dynamodb = boto3.client("dynamodb")
s3 = boto3.client('s3')
print("hola7")
def get_user_info_from_trips(trip_list):
    """method to get user info for a set of trips"""
    user_id_list = []
    user_info_dict = {}
    for trip in trip_list:
        if {"user_id": {"S": trip["driver_id"]}} not in user_id_list:
            user_id_list.append({"user_id": {"S": trip["driver_id"]}})
    user_info_response = dynamodb.batch_get_item(
        RequestItems={USERS_TABLE:{'Keys': user_id_list}})["Responses"]["users"]
    for trip in trip_list:
        for user_info in user_info_response:
            if trip["driver_id"] == user_info["user_id"]["S"]:
                user_info_dict["name"] = user_info["name"]["S"]
                user_info_dict["verified"] = user_info["verified"]["BOOL"]
                if user_info["picture"]["S"]:
                    user_info_dict["picture"] = s3.generate_presigned_url(
                        'get_object', Params = {
                            'Bucket': 'mube-s3bucket', 'Key': user_info["picture"]["S"]},
                        ExpiresIn=3600)
                trip['driver_info'] = deepcopy(user_info_dict)
    return trip_list

def get_user_info_from_tripsb64(trip_list):
    """method to get user info for a set of trips"""
    user_id_list = []
    user_info_dict = {}
    for trip in trip_list:
        if {"user_id": {"S": trip["driver_id"]}} not in user_id_list:
            user_id_list.append({"user_id": {"S": trip["driver_id"]}})
    user_info_response = dynamodb.batch_get_item(
        RequestItems={USERS_TABLE:{'Keys': user_id_list}})["Responses"]["users"]
    for trip in trip_list:
        for user_info in user_info_response:
            if trip["driver_id"] == user_info["user_id"]["S"]:
                user_info_dict["name"] = user_info["name"]["S"]
                if user_info.get("verified"):
                    user_info_dict["verified"] = user_info["verified"]["BOOL"]
                if user_info["picture"]["S"]:
                    response = s3.get_object(
                        Bucket="mube-s3bucket", Key=user_info["picture"]["S"])["Body"].read()
                    user_info_dict["picture"] = b64encode(response).decode("utf-8")
                trip['driver_info'] = deepcopy(user_info_dict)
                user_info_dict.clear()
    return trip_list

def get_user_info_driver(reserved_trips):
    """function to get driver info"""
    driver_ids = [trip['driver_id'] for trip in reserved_trips]
    driver_info = users_table.scan(TableName=USERS_TABLE)
    filtered_driver_info = [info for info in driver_info['Items'] if info['user_id'] in driver_ids]
    driver_info_map = {info['user_id']: {
            'picture': info.get('picture'), 'verified': info.get('verified'),
            'name': info.get('name')} for info in filtered_driver_info}
    for trip in reserved_trips:
        driver_info = driver_info_map.get(trip['driver_id'])
        if driver_info:
            trip['driver_info'] = driver_info
    return reserved_trips

def get_user_info_from_objectb64(user_object):
    """method to get user info for a set of trips"""
    user_info_dict = {}
    user_info_dict["name"] = user_object["name"]
    if user_object.get("verified"):
        user_info_dict["verified"] = user_object["verified"]
    if user_object.get("picture"):
        response = s3.get_object(
            Bucket="mube-s3bucket", Key=user_object["picture"])["Body"].read()
        user_info_dict["picture"] = b64encode(response).decode("utf-8")
    return user_info_dict
