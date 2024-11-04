import unittest
from unittest.mock import patch, MagicMock
from unittest import mock
from botocore.exceptions import ClientError
import pytest
import sys
import os
import uuid
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

class TestLambdaHandler(unittest.TestCase):
    @patch.dict(os.environ, {"stripe_api_key": "test_stripe_key", "reservation_wh_secret": "test_secret"})
    @patch("trips.trip_lambda_reservation.boto3.resource")
    def test_lambda_handler(self, mock_boto3):
        # Retrasamos la importación para que las variables de entorno estén disponibles
        from trips.trip_lambda_reservation import lambda_handler

        # Mocks de las tablas DynamoDB
        mock_users_table = MagicMock()
        mock_user_data_table = MagicMock()
        mock_user_requests_table = MagicMock()
        mock_user_reservations_table = MagicMock()
        mock_trips_table = MagicMock()
        mock_trip_requests_table = MagicMock()
        mock_trip_reservations_table = MagicMock()
        mock_chat_table = MagicMock()
        mock_user_chats_table = MagicMock()

        mock_boto3.return_value.Table.side_effect = [
            mock_users_table,
            mock_user_data_table,
            mock_user_requests_table,
            mock_user_reservations_table,
            mock_trips_table,
            mock_trip_requests_table,
            mock_trip_reservations_table,
            mock_chat_table,
            mock_user_chats_table
        ]

         # Simular el retorno de get_item
        mock_trips_table.get_item.return_value = {
            "Item": {
                "trip_id": "84b42128-a489-43cb-8fe7-e702581281c6",
                "available": True,
                "reservationMode": "manual",
                "status": "pending",
                "driverId": "9a4aabde-32f5-40d6-9a7c-9ea2d85c3432",
                "reservatedSeats": '0',
                "totalSeats": '4',
                "latitudeDeparture": "37.18692862559688",
                "longitudeDeparture": "-3.7108370031861733",
                "latitudeArrival": "37.150101419498796",
                "longitudeArrival": "-3.6087999298537365",
                "vehicleId": '',
                "comment": 'viaje de prueba 1',
                "departureTime": "2024-11-29T18:16:28",
                "departureLocation": "C. Fernando de los Ríos, 55, Local 2, 18320 Santa Fe, Granada",
                "arrivalLocation": "Parque Tecnológico de Ciencias de la Salud, Av. del Conocimiento, 15, 18100, Granada",
                "price": '3',
                "arrivalTime": "2024-11-29T18:46:28"
            }
        }

         # Simular el retorno de get_item
        mock_user_chats_table.get_item.return_value = {
            "user_id": "9a4aabde-32f5-40d6-9a7c-9ea2d85c3432",
            "chat_sessions": [
                {
                    "chat_id": "chat_1"
                }
            ]
        }
        # Evento de entrada simulado
        event = {
             "body-json": {
      "id": "evt_3QCljoCvpYLTdgxQ1vBVDG4R",
      "object": "event",
      "api_version": "2023-10-16",
      "created": 1729617800,
      "data": {
        "object": {
          "id": "pi_3QCljoCvpYLTdgxQ1cXJqVAt",
          "object": "payment_intent",
          "amount": 1400,
          "amount_capturable": 0,
          "amount_details": {
            "tip": {}
          },
          "amount_received": 1400,
          "application": "None",
          "application_fee_amount": "None",
          "automatic_payment_methods": {
            "allow_redirects": "always",
            "enabled": True
          },
          "canceled_at": "None",
          "cancellation_reason": "None",
          "capture_method": "automatic",
          "client_secret": "pi_3QCljoCvpYLTdgxQ1cXJqVAt_secret_n6z9gS3YAgwof45Fa6PcWk7MR",
          "confirmation_method": "automatic",
          "created": 1729617560,
          "currency": "eur",
          "customer": "cus_R4Y3tq7HPmjS0T",
          "description": "None",
          "invoice": "None",
          "last_payment_error": "None",
          "latest_charge": "ch_3QCljoCvpYLTdgxQ1pwSXStr",
          "livemode": False,
          "metadata": {
            "userId": "9a4aabde-32f5-40d6-9a7c-9ea2d85c3432",
            "requiredSeats": "1",
            "tripId": "84b42128-a489-43cb-8fe7-e702581281c6"
          },
          "next_action": "None",
          "on_behalf_of": "None",
          "payment_method": "pm_1QClnfCvpYLTdgxQOpoyEVy1",
          "payment_method_configuration_details": {
            "id": "pmc_1OtTBbCvpYLTdgxQRsAemwtg",
            "parent": "None"
          },
          "payment_method_options": {
            "bancontact": {
              "preferred_language": "en"
            },
            "card": {
              "installments": "None",
              "mandate_options": "None",
              "network": "None",
              "request_three_d_secure": "automatic"
            },
            "eps": {},
            "giropay": {},
            "ideal": {},
            "klarna": {
              "preferred_locale": "None"
            },
            "link": {
              "persistent_token": "None"
            }
          },
          "payment_method_types": [
            "card",
            "bancontact",
            "eps",
            "giropay",
            "ideal",
            "klarna",
            "link"
          ],
          "processing": "None",
          "receipt_email": "None",
          "review": "None",
          "setup_future_usage": "None",
          "shipping": "None",
          "source": "None",
          "statement_descriptor": "None",
          "statement_descriptor_suffix": "None",
          "status": "succeeded",
          "transfer_data": "None",
          "transfer_group": "None"
        }
      },
      "livemode": False,
      "pending_webhooks": 3,
      "request": {
        "id": "req_YUJb9cq1CkerhJ",
        "idempotency_key": "5088cff4-24ad-422d-9c33-92a099f718f1"
      },
      "type": "payment_intent.succeeded"
    }
        }

        # Llamar a la lambda
        response = lambda_handler(event, None)

        # Verificar la respuesta esperada
        expected_response = {'success': True, 'message': None, 'data': [{'available': True, 'reservationMode': 'manual',
                                                                         'status': 'pending', 'driverId': '9a4aabde-32f5-40d6-9a7c-9ea2d85c3432', 
                                                                         'tripId': '84b42128-a489-43cb-8fe7-e702581281c6', 'reservatedSeats': '0',
                                                                         'totalSeats': '4', 'latitudeDeparture': '37.18692862559688', 'latitudeArrival': '37.150101419498796',
                                                                         'longitudeDeparture': '-3.7108370031861733', 'longitudeArrival': '-3.6087999298537365', 'vehicleId': '',
                                                                         'comment': 'viaje de prueba 1', 'departureTime': '2024-11-29T18:16:28',
                                                                         'departureLocation': 'C. Fernando de los Ríos, 55, Local 2, 18320 Santa Fe, Granada',
                                                                         'arrivalLocation': 'Parque Tecnológico de Ciencias de la Salud, Av. del Conocimiento, 15, 18100, Granada',
                                                                         'price': '3', 'arrivalTime': '2024-11-29T18:46:28'}]}
        # Aquí se verifican las respuestas esperadas
        self.assertEqual(response, expected_response)

if __name__ == "__main__":
    unittest.main()


