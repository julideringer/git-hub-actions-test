import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
import sys
import os
import uuid
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from trips.trip_lambda_publication import lambda_handler

class TestLambdaHandler(unittest.TestCase):
    @patch("trips.trip_lambda_publication.boto3.resource")
    @patch("trips.trip_lambda_publication.uuid.uuid4")
    @patch("trips.trip_lambda_publication.datetime")
    def test_lambda_handler(self, mock_datetime, mock_uuid, mock_boto3):
        # Configuración de los mocks
        mock_uuid.return_value = uuid.UUID('12345678123456781234567812345678')
        mock_datetime.now.return_value = datetime(2024, 9, 20, 20, 0, 28)

        # Mocks de las tablas DynamoDB
        mock_trips_table = MagicMock()
        mock_boto3.return_value.Table.side_effect = [mock_trips_table]
        # Evento de entrada simulado
        event = {
            "body-json": {
                "vehicleId": "",
                "userId": "f8a6fc06-5380-4341-bd4d-4baed15fd9dd",
                'departureLocation': 'C. Fernando de los Ríos, 55, Local 2, 18320 Santa Fe, Granada',
                "arrivalLocation":  "Parque Tecnológico de Ciencias de la Salud, Av. del Conocimiento, 15, 18100, Granada",
                "arrivalTime": "2024-09-20T20:00:28",
                "latitudDeparture": "37.18692862559688",
                "longitudDeparture": "-3.7108370031861733",
                "latitudArrival": "37.150101419498796",
                "longitudArrival": "-3.6087999298537365",
                "totalSeats": "4",
                "price": "3",
                "departureTime": "2024-09-20T20:00:28",
                "comment": "me gusta la gente amable y no fumadora",
                "reservationMode": "auto"
            }
        }

        # Llamar a la lambda
        response = lambda_handler(event)

        expected_body = {
            'driver_id': 'f8a6fc06-5380-4341-bd4d-4baed15fd9dd',
            'vehicle_id': '',
            'departure_location': 'C. Fernando de los Ríos, 55, Local 2, 18320 Santa Fe, Granada',
            'arrival_location': 'Parque Tecnológico de Ciencias de la Salud, Av. del Conocimiento, 15, 18100, Granada',
            'latitude_departure': '37.18692862559688',
            'longitude_departure': '-3.7108370031861733',
            'latitude_arrival': '37.150101419498796',
            'longitude_arrival': '-3.6087999298537365',
            'departure_time': '2024-09-20T20:00:28',
            'arrival_time': '2024-09-20T20:00:28',
            'total_seats': '4',
            'comment': 'me gusta la gente amable y no fumadora',
            'price': '3',
            'reservation_mode': 'auto',
            'trip_id': unittest.mock.ANY,  # Ignora el valor exacto del trip_id
            'geohash_departure': 'eyt7e',
            'geohash_arrival': 'eyt7m',
            'status': 'pending',
            'reservated_seats': '0',
            'remaining_seats': '4',
            'available': True,
            'creation_date': unittest.mock.ANY
        }

        # Verificar la respuesta esperada
        expected_response = {
            "success": True,
                "message": f'Trip 12345678-1234-5678-1234-567812345678 has been published successfully',
                "data": None
        }

        # Aquí se verifican las respuestas esperadas
        self.assertEqual(response, expected_response)

if __name__ == "__main__":
    unittest.main()