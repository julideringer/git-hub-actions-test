"""Lambda function to handle sign_up process"""
import os
import base64
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
from PIL import Image
from common_tools.payload_parser import success_return_parser, error_return_parser

USERS_TABLE = "users"

client = boto3.client("cognito-idp", os.environ["region_name"])
s3 = boto3.client("s3")
users_table = boto3.resource("dynamodb", region_name=os.environ["region_name"]).Table(USERS_TABLE)

def cognito_update_user(**kwargs):
    """This method disable a user registered with Amazon Cognito"""
    response = client.update_user_attributes(**kwargs["kwargs"])
    return response

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

def update_cognito_data(user_params, user_id):
    """function to handle cognito data update"""
    parsed_data = {
        "Username": user_id,
        "UserAttributes": []
    }
    if user_params.get("name"):
        parsed_data["UserAttributes"].append({
            "Name": "name",
            "Value": user_params.get("name")})
    #if user_params.get("lastName"):
    #    parsed_data["UserAttributes"].append({
    #        "Name": "name",
    #        "Value": user_params.get("name")})
    if user_params.get("gender"):
        parsed_data["UserAttributes"].append({
            "Name": "gender",
            "Value": user_params.get("gender")})
    if user_params.get("birthdate"):
        parsed_data["UserAttributes"].append({
            "Name": "birthdate",
            "Value": user_params.get("birthdate")})
    if user_params.get("email"):
        parsed_data["UserAttributes"].append({
            "Name": "email",
            "Value": user_params.get("email")})
        parsed_data["UserAttributes"].append({
            "Name": "email_verified",
            "Value": "false"})
    if user_params.get("phone_number"):
        parsed_data["UserAttributes"].append({
            "Name": "phone_number",
            "Value": user_params.get("phone_number")})
        parsed_data["UserAttributes"].append({
            "Name": "phone_number_verified",
            "Value": "false"})
    if user_params.get("biography"):
        parsed_data["UserAttributes"].append({
            "Name": "custom:biography",
            "Value": user_params.get("biography")})
    if user_params.get("picture"):
        picture_key = update_profile_picture(
            user_id, user_params["picture"])
        parsed_data["UserAttributes"].append({
            "Name": "picture",
            "Value": picture_key
        })
    admin_update_user(kwargs=parsed_data)

def update_dynamodb_user(user_params, user_id):
    """function to handle dynamodb user data"""
    update_expression_list = []
    expression_attribute_names = {}
    expression_attribute_values = {}

    if user_params.get("name"):
        update_expression_list.append("#name = :name")
        expression_attribute_names["#name"] = "name"
        expression_attribute_values[":name"] = user_params["name"]
    if user_params.get("lastName"):
        update_expression_list.append("#last_name = :last_name")
        expression_attribute_names["#last_name"] = "last_name"
        expression_attribute_values[":last_name"] = user_params["lastName"]
    if user_params.get("gender"):
        update_expression_list.append("#gender = :gender")
        expression_attribute_names["#gender"] = "gender"
        expression_attribute_values[":gender"] = user_params["gender"]
    if user_params.get("birthdate"):
        update_expression_list.append("#birthdate = :birthdate")
        expression_attribute_names["#birthdate"] = "birthdate"
        expression_attribute_values[":birthdate"] = user_params["birthdate"]
    if user_params.get("email"):
        update_expression_list.append("#email = :email")
        expression_attribute_names["#email"] = "email"
        expression_attribute_values[":email"] = user_params["email"]
        update_expression_list.append("#verified = :verified")
        expression_attribute_names["#verified"] = "verified"
        expression_attribute_values[":verified"] = False
    if user_params.get("phone_number"):
        update_expression_list.append("#phone_number = :phone_number")
        expression_attribute_names["#phone_number"] = "phone_number"
        expression_attribute_values[":phone_number"] = user_params["phoneNumber"]
    if user_params.get("biography"):
        update_expression_list.append("#biography = :biography")
        expression_attribute_names["#biography"] = "biography"
        expression_attribute_values[":biography"] = user_params["biography"]
    if user_params.get("picture"):
        update_expression_list.append("#picture = :picture")
        expression_attribute_names["#picture"] = "picture"
        expression_attribute_values[":picture"] = f"user_images/{user_id}/{user_id}.jpg"
    update_expression = "set "
    update_expression += update_expression_list[0]
    for item in update_expression_list[1:]:
        update_expression += ", " + item
    users_table.update_item(
        Key={"user_id": user_id},
        UpdateExpression = update_expression,
        ExpressionAttributeNames = expression_attribute_names,
        ExpressionAttributeValues = expression_attribute_values)

def lambda_handler(event, context) -> str:
    """lambda handler"""
    user_id = event["params"]["path"]["id"]
    try:
        update_cognito_data(event["body-json"], user_id)
        update_dynamodb_user(event["body-json"], user_id)
        return success_return_parser(
            f"Updated attributes for user {user_id}", None)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
