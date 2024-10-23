"""tool library to parse trip response"""

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
       "arrival_time": trip["arrival_time"],
       "departure_location": trip["departure_location"],
       "arrival_location": trip["arrival_location"],
       "price": trip["price"],
    }
    if "passengers_info" in trip:
        trip_response["passengers_info"] = trip["passengers_info"]
    if "requests_info" in trip:
        trip_response["requests_info"] = trip["requests_info"]
    return trip_response
