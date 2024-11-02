"""tool library to parse trip response"""

def parser_to_snake_case(raw_item):
    """lambda function to parse to camel case"""
    return {
        "driver_id": raw_item["userId"],
        "vehicle_id": raw_item["vehicleId"],
        "departure_location": raw_item["departureLocation"],
        "arrival_location": raw_item["arrivalLocation"],
        "latitude_departure": raw_item["latitudDeparture"],
        "longitude_departure": raw_item["longitudDeparture"],
        "latitude_arrival": raw_item["latitudArrival"],
        "longitude_arrival": raw_item["longitudArrival"],
        "departure_time": raw_item["departureTime"],
        "arrival_time": raw_item["arrivalTime"],
        "total_seats": raw_item["totalSeats"],
        "comment": raw_item["comment"],
        "price": raw_item["price"],
        "reservation_mode": raw_item["reservationMode"],
    }

def response_trip_parser(trip):
    """function to parse the trip response"""
    trip_response = {
       "available": trip["available"],
       "reservation_mode": trip["reservation_mode"],
       "status": trip["status"],
       "driver_id": trip["driver_id"],
       "trip_id": trip["trip_id"],
       "reservated_seats": trip["reservated_seats"],
       "total_seats": trip["total_seats"],
       "latitude_departure": trip["latitude_departure"],
       "latitude_arrival": trip["latitude_arrival"],
       "longitude_departure": trip["longitude_departure"],
       "longitude_arrival": trip["longitude_arrival"],
       "vehicle_id": trip["vehicle_id"],
       "comment": trip["comment"],
       "departure_time": trip["departure_time"],
       "departure_location": trip["departure_location"],
       "arrival_location": trip["arrival_location"],
       "price": trip["price"],
    }
    if "arrival_time" in trip:
        trip_response["arrival_time"] = trip["arrival_time"]
    if "passengers_info" in trip:
        trip_response["passengers_info"] = trip["passengers_info"]
    if "requests_info" in trip:
        trip_response["requests_info"] = trip["requests_info"]
    return trip_response
