"""SDK for dictionary parser to camel case"""
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

def to_camel_case(snake_str):
    """to lower camel case"""
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))

def to_lower_camel_case(snake_str):
    """to lower camel case"""
    camel_string = to_camel_case(snake_str)
    return snake_str[0].lower() + camel_string[1:]

def dict_parser_to_camel_case(body):
    """dict parser to camel case"""
    parsed_body = {}
    for key, value in body.items():
        parsed_key = to_lower_camel_case(key)
        parsed_body[parsed_key] = value
    return parsed_body
