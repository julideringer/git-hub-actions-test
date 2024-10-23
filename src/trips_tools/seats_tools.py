"""module to store all the trips tools"""

def required_seats_function(required_seats, remaining_seats, reserved_seats):
    """function to determine if there free seats or not"""
    trip_available = True
    if required_seats <= remaining_seats:
        reserved_seats_update = required_seats + reserved_seats
        remaining_seats_update = remaining_seats - required_seats
        if remaining_seats_update == 0:
            trip_available = False
        update_expression = "SET reservated_seats = :val1,\
                                remaining_seats = :val2, available = :val3"
        expression_attribute_values = {
            ":val1": str(reserved_seats_update),
            ":val2": str(remaining_seats_update),
            ":val3": trip_available
        }
        return {"success": True, "data": [update_expression, expression_attribute_values]}
    return {"success": False, "error_message": "unavailable number of required seats", "data": None}

def get_updated_seats(total_reserved_seats, remaining_seats, reserved_seats):
    """function to determine if there free seats or not"""
    trip_available = True
    reserved_seats_update = total_reserved_seats - reserved_seats
    remaining_seats_update = remaining_seats + reserved_seats
    if remaining_seats_update == 0:
        trip_available = False
    return {
        "reservated_seats": reserved_seats_update,
        "remaining_seats": remaining_seats,
        "available": trip_available
    }
