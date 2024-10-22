"""lambda function for trip reservation"""
import os
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
import geohash

trips_table = boto3.resource("dynamodb").Table('trips')
routines_table = boto3.resource("dynamodb").Table('routines')
users_table = boto3.resource("dynamodb").Table('users')

def lambda_handler(event, context= None):
    """lambda handler"""
    trip_id = event['body-json']['tripId']
    origen = event['body-json']['departureLocation']
    destino = event['body-json']['arrivalLocation']
    fecha = event['body-json']['departureTime']
    trip = trips_table.get_item(Key={'trip_id': trip_id})
    reservated_seats = trip['Item']['reservated_seats']

    try:
        # Validar que se proporciona al menos un campo para actualizar
        if not (origen or destino or fecha):
            return {
            "success": False,
            'error_message': "At least one field must be provided for updating",
            "data": None
            
        }
        #Si no hay ningun pasajero se podra modfiicar, itenario , fecha , hora, precio, modo reserva, numero asientos, detalles del viaje
        if reservated_seats == "0":
            # Crear la expresión de actualización y los valores de atributos de expresión
            update_expression = 'SET'
            expression_attribute_values = {}
            if origen:
                update_expression += ' departure_location = :o,'
                expression_attribute_values[':o'] = origen
            if destino:
                update_expression += ' arrival_location = :d,'
                expression_attribute_values[':d'] = destino
            if fecha:
                update_expression += ' departure_time = :f,'
                expression_attribute_values[':f'] = fecha

            # Eliminar la coma adicional al final de la expresión de actualización
            update_expression = update_expression.rstrip(',')

            trips_table.update_item(
                    Key={'trip_id': trip_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values)
        
            body = {"success": True,
                    "data": {
                        "message": f'Trip {trip_id} has been modified successfully',
                        "info": None
            }}
        #Si hay pasajeros que ya han reservado se podrá modificar el precio, modo de reserva, numero de asientos    
        else:
            # Crear la expresión de actualización y los valores de atributos de expresión
            update_expression = 'SET'
            expression_attribute_values = {}
            if origen:
                update_expression += ' departure_location = :o,'
                expression_attribute_values[':o'] = origen
            if destino:
                update_expression += ' arrival_location = :d,'
                expression_attribute_values[':d'] = destino
            if fecha:
                update_expression += ' departure_time = :f,'
                expression_attribute_values[':f'] = fecha

            # Eliminar la coma adicional al final de la expresión de actualización
            update_expression = update_expression.rstrip(',')

            trips_table.update_item(
                    Key={'trip_id': trip_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values)
        
            body = {"success": True,
                    "data": {
                        "message": f'Trip {trip_id} has been modified successfully',
                        "info": None
            }}
    except ClientError as error:
        body = {
            "success": False,
            "error_message": error.response['Error']['Message'],
            "error_code": error.response['Error']['Code'],
            "data": None
        }
    return body

