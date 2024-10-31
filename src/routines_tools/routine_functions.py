"""Library to store all the suppor functions for routine"""
import uuid
import json
import copy

def parse_sqs_batch_item_format(raw_item, departure_time):
    """function to parse the items to dynamodb format"""
    raw_item['trip_id'] = str(uuid.uuid4())
    raw_item['departure_time'] = departure_time
    raw_item['available'] = True
    raw_item['status'] = 'pending'
    raw_item['price'] = float(raw_item['price'])
    item = {
        'Id': copy.deepcopy(raw_item.get('trip_id')),
        'MessageBody': json.dumps(raw_item),
        'DelaySeconds': 1
    }
    return item

def split_list(lst, sublist_size):
    """function to split lists in sublist"""
    return [lst[i:i+sublist_size] for i in range(0, len(lst), sublist_size)]

def parser_to_snake_case(raw_item):
    """lambda function to parse to camel case"""
    return {
        'user_id': raw_item['userId'],
        'vehicle_id': raw_item['vehicleId'],
        'departure_location': raw_item['departureLocation'],
        'arrival_location': raw_item['arrivalLocation'],
        'latitude_departure': raw_item['latitudDeparture'],
        'longitude_departure': raw_item['longitudDeparture'],
        'latitude_arrival': raw_item['latitudArrival'],
        'longitude_arrival': raw_item['longitudArrival'],
        'departure_time': raw_item['departureTime'],
        'total_seats': raw_item['totalSeats'],
        'comment': raw_item['comment'],
        'price': raw_item['price'],
        'reservation_mode': raw_item['reservationMode'],
        'description': raw_item['description']
    }

def parser_to_dynamodb_case_routines(raw_item):
    """lambda function to parse to dynamodb case"""
    return {
        'routine_id': {"S": raw_item['routine_id']},
        'driver_id': {"S": raw_item['driver_id']},
        'vehicle_id': {"S": raw_item['vehicle_id']},
        'departure_location': {"S": raw_item['departure_location']},
        'arrival_location': {"S": raw_item['arrival_location']},
        'latitude_departure': {"S": raw_item['latitude_departure']},
        'longitude_departure': {"S": raw_item['longitude_departure']},
        'latitude_arrival': {"S": raw_item['latitude_arrival']},
        'longitude_arrival': {"S": raw_item['longitude_arrival']},
        'geohash_departure': {"S": raw_item['geohash_departure']},
        'geohash_arrival': {"S": raw_item['geohash_arrival']},
        'total_seats': {"S": raw_item['total_seats']},
        'remaining_seats': {"S": raw_item['remaining_seats']},
        'reservated_seats': {"S": raw_item['reservated_seats']},
        'comment': {"S": raw_item['comment']},
        'price': {"N": raw_item['price']},
        'reservation_mode': {"S": raw_item['reservation_mode']},
        'description': {"S": raw_item['description']}
    }
