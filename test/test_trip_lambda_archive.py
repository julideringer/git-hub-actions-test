import unittest
import sys
import os

# Añadir la ruta de src al PYTHONPATH para importar correctamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from trips.trip_lambda_archive import lambda_handler  # Asegúrate de importar correctamente

class TestLambdaHandler(unittest.TestCase):

    def test_lambda_handler(self):
        # Ejecutar el lambda_handler sin contexto ni evento
        response = lambda_handler()

        # Verificaciones
        self.assertIsInstance(response, dict)  # Comprobar que la respuesta es un diccionario
        self.assertIn('success', response)  # Verificar que 'success' está en la respuesta
        self.assertIsInstance(response['success'], bool)  # Asegurar que 'success' es booleano

if __name__ == '__main__':
    unittest.main()
