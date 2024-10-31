"""script to send money to connected account"""

import stripe

stripe.api_key = "sk_test_51OhwUsCvpYLTdgxQq9Vuo87nkTzJqDTywVioThhFt2eMdrnZTGHWiwdeCvG4ttTA9nwiCp87gR4P7MyO1hjXAZuo00U7G7Aoxc"
ACCOUNT_ID = "acct_1Pg7SzCvffCkFx8q"  # Reemplaza con tu Connected Account ID

payment_method = stripe.PaymentMethod.create(
    type="card",
    card={
        "number": "4000000000000077",
        "exp_month": 12,
        "exp_year": 2024,
        "cvc": "123",
    },
    billing_details={"name": "John Doe"},
)

print(payment_method)
