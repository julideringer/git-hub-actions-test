"""file with parser functions"""

def success_return_parser(message, data):
    """function to parse the successfull return payload"""
    return {"success": True,
            "message": message,
            "data": data}

def error_return_parser(message, code):
    """function to parse the return error payload"""
    return {"success": False,
            "message": message,
            "code": code}
