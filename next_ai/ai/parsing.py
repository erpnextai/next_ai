import frappe
from pydantic import BaseModel, Field, create_model
from next_ai.ai.utils import get_parser_type_details


@frappe.whitelist(methods=["POST"])
def get_ai_parser_response(**kwargs):
    """
    doctype: str - The name of the doctype to parse data for.
    name: str - The name of the document instance.
    message: str - The user input message to be parsed.
    """
    message = NextAIParsing().get_response(kwargs)
    return {"status_code":200, "status": "sucess", "message": message}

@frappe.whitelist(methods=["GET"])
def get_parser_fieldtype_details():
    parser_type_details = get_parser_type_details()
    return {"status_code":200, "status": "sucess", "message": parser_type_details}


class NextAIParsing:
    """
    This class is mainly used to get the user input and parse the data inside the doctype fields.
    """
    def __init__(self):
        pass

    def get_response(self, data) -> dict:
        doctype = data.get("doctype")
        doctype_name = data.get("name")
        message = data.get("message")

        return {'status': 'Open', 'description': 'Parsed Data', 'priority': 'High'}
    

    def build_dynamic_parser(fields: dict):
        model_fields = {}

        for name, meta in fields.items():
            field_type = meta["type"]
            description = meta.get("description", "")

            # Add field with default None (or False for bool)
            default_value = False if field_type is bool else None

            model_fields[name] = (field_type, Field(default_value, description=description))

        # dynamically create a pydantic model
        DynamicBaseParser = create_model("DynamicBaseParser", **model_fields)
        return DynamicBaseParser

    def test_dynamic_parser(self):
        fields = {
            "status": {"type": str, "description": "Status of the task"},
            "description": {"type": str, "description": "Description of the task"},
            "priority": {"type": str, "description": "Priority level"},
            "is_completed": {"type": bool, "description": "Completion status"}
        }

        DynamicParser = self.build_dynamic_parser(fields)

        # Example usage
        example_data = {
            "status": "Open",
            "description": "This is a test task.",
            "priority": "High",
            "is_completed": False
        }

        parsed_instance = DynamicParser(**example_data)
        frappe.logger().info(f"Parsed Instance: {parsed_instance}")
        return parsed_instance


    def get_parsing_field_details(self, name) -> dict:
        """
        Get the field details for a given parser field name.
        """
        pass