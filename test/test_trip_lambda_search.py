import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
import sys
import os
import uuid
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from trips.trip_lambda_search import lambda_handler

class TestLambdaHandler(unittest.TestCase):
    @patch("trips.trip_lambda_search.boto3.resource")
    def test_lambda_handler(self, mock_boto3):

        # Mocks de las tablas DynamoDB
        mock_trips_table = MagicMock()
        mock_boto3.return_value.Table.side_effect = [mock_trips_table]
        # Evento de entrada simulado
        event = {
            "body-json": {
                "userId": "7eb03f45-391e-4fd1-931c-7796caa05df1",
                "passengers": 1,
                "departureLocation": "C. Fernando de los Ríos, 55, Local 2, 18320 Santa Fe, Granada",
                "arrivalLocation":  "Parque Tecnológico de Ciencias de la Salud, Av. del Conocimiento, 15, 18100, Granada",
                "latitudDeparture": "37.18692862559688",
                "longitudDeparture": "-3.7108370031861733",
                "latitudArrival": "37.150101419498796",
                "longitudArrival": "-3.6087999298537365",
                "arrivalTime": "2024-11-29T18:46:28",
                "departureTime": "2024-11-29T18:16:28"
            }
        }

        # Llamar a la lambda
        response = lambda_handler(event)

        # Verificar la respuesta esperada
        expected_response = {
            'success': True,
            'message': None,
            'data': [
                        {
                            'available': True,
                            'reservationMode': 'manual',
                            'status': 'pending',
                            'driverId': '9a4aabde-32f5-40d6-9a7c-9ea2d85c3432',
                            'tripId': '84b42128-a489-43cb-8fe7-e702581281c6',
                            'reservatedSeats': '0',
                            'totalSeats': '4',
                            'latitudeDeparture': '37.18692862559688',
                            'latitudeArrival': '37.150101419498796',
                            'longitudeDeparture': '-3.7108370031861733',
                            'longitudeArrival': '-3.6087999298537365',
                            'vehicleId': '',
                            'comment': 'viaje de prueba 1',
                            'departureTime': '2024-11-29T18:16:28',
                            'departureLocation': 'C. Fernando de los Ríos, 55, Local 2, 18320 Santa Fe, Granada',
                            'arrivalLocation': 'Parque Tecnológico de Ciencias de la Salud, Av. del Conocimiento, 15, 18100, Granada',
                            'price': '3',
                            'arrivalTime': '2024-11-29T18:46:28',
                            
                        }
                    ]
        }

        # Aquí se verifican las respuestas esperadas
        self.assertEqual(response, expected_response)

if __name__ == "__main__":
    unittest.main()
