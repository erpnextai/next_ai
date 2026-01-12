import frappe
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from frappe import _
from pydantic import BaseModel, Field, create_model
from next_ai.ai.utils import get_parser_type_details
from next_ai.ai.prompt import PARSING_PROMPT


@frappe.whitelist(methods=["POST"])
def get_ai_parser_response(**kwargs):
    """
    doctype: str - The name of the doctype to parse data for.
    name: str - The name of the document instance.
    message: str - The user input message to be parsed.
    """
    data = frappe._dict(kwargs)

    # Mandatory fields
    required_fields = ["doctype", "name", "message"]

    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        frappe.throw(f"Missing mandatory fields: {', '.join(missing)}")

    message = NextAIParsing(api_data=data).get_response()
    return {"status_code":200, "status": "sucess", "message": message}


@frappe.whitelist(methods=["GET"])
def get_parser_fieldtype_details():
    parser_type_details = get_parser_type_details()
    return {"status_code":200, "status": "sucess", "message": parser_type_details}


class NextAIParsing:
    """
    This class is mainly used to get the user input and parse the data inside the doctype fields.
    """
    def __init__(self, api_data: dict):
        self.api_data = api_data

        self.message = self.api_data.get("message")

        self.parsing_fields = self.get_parsing_field_details()
        self.field_meta = get_parser_type_details()

        self.nextai_settings = self.get_nextai_settings()
        self.validate_settings()

        self.current_model = self.nextai_settings.model_name

    def validate_token(self):
        if len(self.api_data['message']) > 8000:
            frappe.throw(_("Prompt length exceeds the maximum limit of 8000 characters. Please shorten your prompt."))
    
    def validate_settings(self):
        if not self.nextai_settings.model_name:
            frappe.throw(_("Model name is not set in NextAI Settings. Please configure the model name."))
        if not self.nextai_settings.platform:
            frappe.throw(_("Platform is not set in NextAI Settings. Please configure the platform."))
        if not self.nextai_settings.get_password("api_key"):
            frappe.throw(_("API Key is not set in NextAI Settings. Please configure the API Key."))
    
    def get_nextai_settings(self):
        nextai_settings = frappe.get_doc('NextAI Settings')
        return nextai_settings
    
    def get_llm(self, model_name: str = None):
        model_name = model_name or self.nextai_settings.model_name
        try:
            if self.nextai_settings.platform == 'Gemini':
                os.environ['GOOGLE_API_KEY'] = self.nextai_settings.get_password("api_key")
                llm = ChatGoogleGenerativeAI(model=model_name)
                return llm
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error in NextAIParsing.get_llm")
            frappe.throw(_("Error in getting LLM: {0}").format(str(e)))

    def get_structured_output_llm(self, model_name: str = None, base_model: BaseModel = None):
        llm = self.get_llm(model_name=model_name)
        so_llm = llm.with_structured_output(base_model)
        return so_llm
    
    def get_prompt_message(self) -> str:
        prompt = PARSING_PROMPT.format(input=self.message)
        return prompt

    def get_response(self) -> dict:
        DynamicBaseParser = self.build_dynamic_parser()
        so_llm = self.get_structured_output_llm(model_name=self.current_model, base_model=DynamicBaseParser)
        message = self.get_prompt_message()
        response = so_llm.invoke(message)
        response = response.__dict__
        return response

    def build_dynamic_parser(self):
        model_fields = {}
        
        for field_details in self.parsing_fields:
            fields_type_detail = self.field_meta.get(field_details['field_type'])
            if not fields_type_detail['is_active']:
                continue

            model_fields[field_details['field_name']] = {}
            _type, default_description = fields_type_detail['type'], fields_type_detail['default_description']

            model_fields[field_details['field_name']]['type'] = _type
            model_fields[field_details['field_name']]['description'] = field_details.get('description') or default_description

            default_value = None

            model_fields[field_details['field_name']] = (
                _type,
                Field(default_value, description=model_fields[field_details['field_name']]['description'])
            )
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


    def get_parsing_field_details(self) -> dict:
        """
        Get the field details for a given parser field name.
        """
        data = frappe.db.get_all(
            "NextAI Parsing Details",
            filters={
                "parenttype": "NextAI Parsing",
                "parentfield": "parsing_details",
                "parent": self.api_data.get("name"),
            },
            fields=['*'],
            order_by='idx'
        )
        return data