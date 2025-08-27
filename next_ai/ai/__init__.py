import os
import frappe
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import ResourceExhausted
from frappe import _
from next_ai.ai.prompt import PROMPTS
from next_ai.ai.structured_output import NEXTAIBaseModel



@frappe.whitelist(allow_guest=True)
def test_gemini(**kwargs):

    if "GOOGLE_API_KEY" not in os.environ:
        return {"status": "error", "message": "GOOGLE_API_KEY not set in environment variables"}

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        # other params...
    )

    messages = [
        (
            "system",
            "You are name is Next AI & Introduce like you Next AI. Ensure that you are working fine. giving a worm welcome to the user. In a simple text format only",
        ),
        ("human", "Who are you?"),
    ]
    ai_msg = llm.invoke(messages)
    ai_msg
    return {"status": "success", "message": ai_msg.content}


@frappe.whitelist(methods=["POST"])
def get_ai_response(**kwargs):
    nextai_llm = NextAILLM(template=PROMPTS[kwargs['type']], user_input=kwargs['value'], field_info=kwargs)
    message = nextai_llm.get_llm_response()
    return {"status_code":200, "status": "sucess", "message": message}


def get_delay_info(model_info, is_subscription, is_free):
    try:
        if is_subscription:
            delay = round(60/model_info.get('subscription_rpm'), 2)
        elif is_free:
            delay = round(60/model_info.get('free_rpm'), 2)
        else:
            delay = 3
    except ZeroDivisionError as e:
        delay = 3

    if not delay:
        frappe.throw(_("Delay information not found for the selected model."))

    return delay


class NextAILLM:
    def __init__(self, template: str = None, user_input: str = None, field_info: dict = None):

        self.template = template
        self.user_input = user_input
        self.field_info = field_info

        self.prompt = self.get_prompt() or template.format(input=user_input)
        self.validate_token()

        self.nextai_settings = self.get_nextai_settings()
        self.validate_settings()

        self.current_model = self.nextai_settings.model_name
        self.model_info = self.get_model_info()
        self.validate_model_info()

    def validate_model_info(self):
        if not self.model_info:
            frappe.log_error(frappe.get_traceback(), "No Active Model Info Found in NextAILLM.validate_model_info")
            frappe.throw(_("No active model info found for the platform {0}. Check NextAI Model Info Doctype.").format(self.nextai_settings.platform))
    
    def validate_token(self):
        if len(self.prompt) > 8000:
            frappe.throw(_("Prompt length exceeds the maximum limit of 8000 characters. Please shorten your prompt."))
    
    def validate_settings(self):
        if not self.nextai_settings.model_name:
            frappe.throw(_("Model name is not set in NextAI Settings. Please configure the model name."))
        if not self.nextai_settings.platform:
            frappe.throw(_("Platform is not set in NextAI Settings. Please configure the platform."))
        if not self.nextai_settings.get_password("api_key"):
            frappe.throw(_("API Key is not set in NextAI Settings. Please configure the API Key."))
    
    def get_prompt(self):
        
        if self.field_info.get('doctype'):
            query = f"""
            SELECT
                ref_doctype, field_name, field_type, prompt, is_user_specific
            FROM
                `tabNextAI Prompt`
            WHERE
                ref_doctype='{self.field_info.get('doctype')}'
                AND field_name='{self.field_info.get('key')}'
                AND user='{frappe.session.user}'
                AND enable=1
                AND is_user_specific=1
            
            UNION ALL

            SELECT
                ref_doctype, field_name, field_type, prompt, is_user_specific
            FROM
                `tabNextAI Prompt`
            WHERE
                ref_doctype='{self.field_info.get('doctype')}'
                AND field_name='{self.field_info.get('key')}'
                AND enable=1
                AND is_user_specific=0
            """
            prompt_list = frappe.db.sql(query, as_dict=True)
            user_prompt = global_prompt = None 
            for prompt in prompt_list:
                if prompt['is_user_specific']:
                    user_prompt = prompt['prompt']
                else:
                    global_prompt = prompt['prompt']
            if user_prompt:
                return user_prompt.format(input=self.user_input)
            elif global_prompt:
                return global_prompt.format(input=self.user_input)
        
    def get_nextai_settings(self):
        nextai_settings = frappe.get_doc('NextAI Settings')
        return nextai_settings

    def get_model_info(self):
        model_info = frappe.db.get_list(
            'NextAI Model Info',
            fields=['*'],
            filters={
                'platform': self.nextai_settings.platform,
                'is_active': 1
            },
            order_by='creation desc'
        )
        if not model_info:
            frappe.log_error(frappe.get_traceback(), "No Active Model Info Found in NextAILLM.get_model_info")
            frappe.throw(_(f"No active model info found for the platform {self.nextai_settings.platform}. Check NextAI Model Info Doctype."))
        return model_info

    def get_llm(self, model_name: str = None):
        model_name = model_name or self.nextai_settings.model_name
        try:
            if self.nextai_settings.platform == 'Gemini':
                os.environ['GOOGLE_API_KEY'] = self.nextai_settings.get_password("api_key")
                llm = ChatGoogleGenerativeAI(model=model_name)
                return llm
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Error in NextAILLM.get_llm")
            frappe.throw(_("Error in getting LLM: {0}").format(str(e)))
    
    def get_structured_output_llm(self, model_name: str = None):
        llm = self.get_llm(model_name=model_name)
        so_llm = llm.with_structured_output(NEXTAIBaseModel)
        return so_llm

    def get_next_model(self, current_model: str = None) -> str:
        is_next = False
        for model in self.model_info:
            if model['model_name'] == current_model:
                is_next = True
                continue
            if is_next:
                return model['model_name']
        return self.model_info[0]['model_name']
    
    def get_llm_response(self, model_name: str = None) -> str:
        try:
            so_llm = self.get_structured_output_llm(model_name=model_name)
            ai_msg = so_llm.invoke(self.prompt)
            return ai_msg.response
        except ResourceExhausted as e:
            frappe.log_error(frappe.get_traceback(), f"RPM limit reached {self.current_model} in NextAILLM.get_llm_response")
            if self.nextai_settings.auto_switch_model_on_rpm:
                self.current_model = self.get_next_model(self.current_model)
                if self.current_model == self.nextai_settings.model_name:
                    frappe.log_error(frappe.get_traceback(), "RPM limit reached for all models in NextAILLM.get_llm_response")
                    frappe.throw(_("RPM limit reached for all the models. Please try again later. Or Please upgrade your plan."))
                self.nextai_settings.model_name = self.current_model
                self.nextai_settings.save(
                    ignore_permissions=True,
                    ignore_version=True
                )
                return self.get_structured_output_llm(model_name=self.current_model)
            else:
                frappe.throw(_(f"RPM limit reached for the current model {self.current_model}. Please try again later."))