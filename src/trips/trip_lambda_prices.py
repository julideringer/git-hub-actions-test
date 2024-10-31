"""lambda function for trip booking"""
import boto3
from src.common_tools.payload_parser import success_return_parser, error_return_parser

PRICE_TABLE = 'prices'

price_table = boto3.resource('dynamodb').Table(PRICE_TABLE)

def iva_addition(raw_price):
    """function to calculate IVA for passenger"""
    return raw_price * 0.21

def comission_addition(raw_price):
    """function to calculate costs of the travel"""
    return raw_price * 0.1

def calculate_range(distance):
    """function to calculate price range of the trip"""
    if 0 < distance <= 2000:
        return 1.5
    if 2000 < distance <= 5000:
        return 0.5
    if 5000 < distance <= 10000:
        return 0.25
    if 10000 < distance <= 20000:
        return 0.2
    if 20000 < distance <= 35000:
        return 0.15
    if 35000 < distance:
        return 0.1

def lambda_handler(event, context) -> str:
    """lambda handler to book a trip"""
    body = event['params']['querystring']['distance']
    distance = int(body)
    if distance < 0:
        return error_return_parser("Invalid negative integer for price",
                                   "UnexpectedValue")
    price_range = calculate_range(distance)
    raw_price = price_range * float(distance / 1000)
    comission_price = comission_addition(raw_price)
    iva_addition_price = iva_addition(raw_price)
    final_billing =  round(comission_price + iva_addition_price + raw_price, 2)
    return success_return_parser(None, {
        "price": final_billing,
        "minimum": round(final_billing * 0.8, 2),
        "maximum": round(final_billing * 1.2, 2)})
