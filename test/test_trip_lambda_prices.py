import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
import sys
import os
import uuid
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from trips.trip_lambda_prices import lambda_handler

class TestLambdaHandler(unittest.TestCase):
    def test_lambda_handler(self):
        # Evento de entrada simulado
        event = {
            "params": {
                "path": {},
                "querystring": {"distance":"9500"}
            }
        }

        # Llamar a la lambda
        response = lambda_handler(event, context= None)

        # Verificar la respuesta esperada
        expected_response = {
            "success": True,
            "message": None,
            "data": {
                "price": 3.11,
                "minimum": 2.49,
                "maximum": 3.73
            }
        }
        # Aquí se verifican las respuestas esperadas
        self.assertEqual(response, expected_response)

if __name__ == "__main__":
    unittest.main()
