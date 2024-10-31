"""script to send money to connected account"""
import os
import boto3
from botocore.exceptions import ClientError
import stripe
from common_tools.payload_parser import success_return_parser, error_return_parser
from trips_tools.seats_tools import required_seats_function

stripe.api_key = os.environ["stripe_api_key"]

USER_DATA_TABLE = "user_data"
TRIPS_TABLE = "trips"

user_data_table = boto3.resource("dynamodb").Table(USER_DATA_TABLE)
trips_table = boto3.resource("dynamodb").Table(TRIPS_TABLE)

def lambda_handler(event, context):
    """lambda handler"""
    intent_params = event["body-json"]
    try:
        user_data = user_data_table.get_item(Key={"user_id": intent_params["userId"]})["Item"]
        trip_object = trips_table.get_item(Key={"trip_id": intent_params["tripId"]})["Item"]
        response = required_seats_function(int(intent_params["requiredSeats"]),
                                           int(trip_object["reservated_seats"]),
                                           int(trip_object["remaining_seats"]))
        if response["success"] is False:
            error_return_parser("Invalid number of seats", None)
        customer_id = user_data["customer_id"]
        intent = stripe.PaymentIntent.create(
            amount=intent_params["amount"],
            currency="eur",
            metadata={"tripId": intent_params["tripId"],
                      "userId": intent_params["userId"],
                      "requiredSeats": intent_params["requiredSeats"]},
            customer=customer_id,
            automatic_payment_methods={
                'enabled': True,
            }
        )
        return success_return_parser("", {"clientSecret": intent.client_secret})
    except stripe.error.StripeError as e:
        return error_return_parser(e.user_message, None)
    except ClientError as error:
        return error_return_parser(error.response["Error"]["Message"],
                                   error.response["Error"]["Code"])
    except Exception as e:
        return error_return_parser(e, None)
