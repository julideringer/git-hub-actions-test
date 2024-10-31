"""Lambda function to handle sign_up process"""
import os
import base64
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
from PIL import Image

USERS_TABLE = "users"

client = boto3.client("cognito-idp", os.environ["region_name"])
s3 = boto3.client("s3")
users_table = boto3.resource("dynamodb", region_name=os.environ["region_name"]).Table(USERS_TABLE)

def cognito_update_user(**kwargs):
    """This method disable a user registered with Amazon Cognito"""
    response = client.update_user_attributes(**kwargs["kwargs"])
    return response

def dynamodb_update_user(kwargs):
    """method to update user attributes in dynamodb"""
    update_expression = "set "
    expression_attribute_names = {}
    expression_attribute_values = {}
    if kwargs["name"]:
        update_expression += "#nm = :n"
        expression_attribute_names["#nm"] = "name"
        expression_attribute_values[":n"] = kwargs["name"]
    if kwargs["picture"]:
        if kwargs["name"]:
            update_expression += ", "
        update_expression += "#np = :p"
        expression_attribute_names["#np"] = "picture"
        expression_attribute_values[":p"] = kwargs["picture"]
    users_table.update_item(
        Key={"user_id": kwargs["username"]},
        UpdateExpression = update_expression,
        ExpressionAttributeNames = expression_attribute_names,
        ExpressionAttributeValues = expression_attribute_values)

def admin_update_user(**kwargs):
    """method to update user attributes"""
    kwargs["kwargs"]["UserPoolId"] = os.environ["userpool_id"]
    response = client.admin_update_user_attributes(**kwargs["kwargs"])
    return response

def get_image_size(image, quality):
    """function to get the image of the size in bytes"""
    output_buffer = BytesIO()
    image.save(output_buffer, format="JPEG", quality=quality)
    return output_buffer.tell(), output_buffer

def resize_profile_picture(picture):
    """function to resize profile picture"""
    max_size_bytes = 200000
    quality = 85
    resize_factor = 0.9
    picture_data = base64.b64decode(picture)
    image = Image.open(BytesIO(picture_data))
    image_size, output_buffer = get_image_size(image, quality)
    while image_size > max_size_bytes and quality > 10:
        quality -= 5
        image_size, output_buffer = get_image_size(image, quality)
        if image_size > max_size_bytes:
            width, height = image.size
            new_width = int(width * resize_factor)
            new_height = int(height * resize_factor)
            image = image.resize((new_width, new_height), Image.LANCZOS)
            image_size, output_buffer = get_image_size(image, quality)
    output_buffer.seek(0)
    return output_buffer.getvalue()

def update_profile_picture(user_id, picture):
    """function to update profile picture photo"""
    picture = resize_profile_picture(picture)
    bucket_name = "mube-s3bucket"
    picture_key = f"user_images/{user_id}/{user_id}.jpg"
    s3.put_object(
        Bucket=bucket_name, Key = picture_key,
        Body=picture, ContentType="image/jpg")
    return picture_key

def lambda_handler(event, context) -> str:
    """lambda handler"""
    body = event["body-json"]
    user_info_dict = {}
    user_info_dict["username"] = event["body-json"]["username"]
    user_info_dict["name"] = None
    user_info_dict["picture"] = None
    kargs = {
        "Username": body.get("username"),
        "UserAttributes": []
    }
    if body.get("name"):
        kargs["UserAttributes"].append({
            "Name": "name",
            "Value": body.get("name")
        })
        user_info_dict["name"] = body.get("name")
    if body.get("gender"):
        kargs["UserAttributes"].append({
            "Name": "gender",
            "Value": body.get("gender")
        })
    if body.get("birthdate"):
        kargs["UserAttributes"].append({
            "Name": "birthdate",
            "Value": body.get("birthdate")
        })
    if body.get("email"):
        kargs["UserAttributes"].append({
            "Name": "email",
            "Value": body.get("email")
        })
        kargs["UserAttributes"].append({
            "Name": "email_verified",
            "Value": "false"
        })
    if body.get("phone_number"):
        kargs["UserAttributes"].append({
            "Name": "phone_number",
            "Value": body.get("phone_number")
        })
        kargs["UserAttributes"].append({
            "Name": "phone_number_verified",
            "Value": "false"
        })
    if body.get("biography"):
        kargs["UserAttributes"].append({
            "Name": "custom:biography",
            "Value": body.get("biography")
        })
    if body.get("picture"):
        picture_key = update_profile_picture(body.get("username"), body.get("picture"))
        kargs["UserAttributes"].append({
            "Name": "picture",
            "Value": picture_key
        })
        user_info_dict["picture"] = picture_key
    try:
        admin_update_user(kwargs=kargs)
        if user_info_dict["picture"] is not None or user_info_dict["name"] is not None:
            dynamodb_update_user(kwargs=user_info_dict)
        return {"success": True,
                "message": f"Updated attributes for user {body['username']}",
                "data": None}
    except ClientError as error:
        return {"success": False, 
                "message": error.response["Error"]["Message"],
                "code": error.response["Error"]["Code"]}
