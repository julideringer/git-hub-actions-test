"""module to test strip account creation"""

import stripe

stripe.api_key = "sk_test_51OhwUsCvpYLTdgxQq9Vuo87nkTzJqDTywVioThhFt2eM\
  drnZTGHWiwdeCvG4ttTA9nwiCp87gR4P7MyO1hjXAZuo00U7G7Aoxc"

creation_response = stripe.Account.create()
stripe.Account.create(
  country="ES",
  email="daniderginger7@gmail.com",
  controller={
    "fees": {"payer": "application"},
    "losses": {"payments": "application"},
    "stripe_dashboard": {"type": "express"},
  },
)

print(creation_response.stripe_id)
