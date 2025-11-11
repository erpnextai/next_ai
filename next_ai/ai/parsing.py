import frappe


@frappe.whitelist(methods=["POST"])
def get_ai_parser_response(**kwargs):
    message = NextAIParsing().get_response()
    return {"status_code":200, "status": "sucess", "message": message}


class NextAIParsing:
    """
    This class is mainly used to get the user input and parse the data inside the doctype fields.
    """
    def __init__(self):
        pass

    def get_response(self):
        return {'status': 'success', 'Description': 'Parsed Data'}