import os
import frappe
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import ResourceExhausted
from frappe import _
from nextai.ai.prompt import PROMPTS
from nextai.ai.structured_output import NEXTAIBaseModel


@frappe.whitelist(allow_guest=True)
def get_field_info(**kwargs):
    return {"status": "success"}


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
    prompt = PROMPTS[kwargs['type']].format(input=kwargs['value'])
    nextai_llm = NextAILLM(prompt)
    message = nextai_llm.get_llm_response(prompt)
    return {"status_code":200, "status": "sucess", "message": message}


@frappe.whitelist(methods=["POST"])
def get_ai_response_deprecated(**kwargs):
    llm, nextai_settings = get_llm()
    if not llm:
        return {"status": "error", "message": "LLM not configured properly"}
    if llm:
        model_info = frappe.db.get_list(
            'NextAI Model Info',
            fields=['*'],
            filters={
                'name': nextai_settings.model_name
            }
        )
        if not model_info:
            return {"status_code":400, "status": "error", "message": "Model Info found in NextAI Model Info"}
        model_info = model_info[0]
        delay = get_delay_info(model_info, nextai_settings.is_subscription, nextai_settings.is_free)
        time.sleep(delay)
        so_llm = llm.with_structured_output(NEXTAIBaseModel)
        prompt = PROMPTS[kwargs['type']].format(input=kwargs['value'])
        ai_msg = so_llm.invoke(prompt)
    return {"status_code":200, "status": "sucess", "message": ai_msg.response}


def get_llm():
    doc = frappe.get_doc('NextAI Settings')
    llm = None

    nextai_llm = NextAILLM()
    llm = nextai_llm.get_llm()
    try:
        if doc.platform == 'Gemini':
            os.environ['GOOGLE_API_KEY'] = doc.get_password("api_key")
            # llm = ChatGoogleGenerativeAI(
            #     model=doc.model_name,
            #     temperature=0,
            #     max_tokens=None,
            #     timeout=None,
            #     max_retries=2,
            # )
            llm = ChatGoogleGenerativeAI(model=doc.model_name)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error in get_llm")
        frappe.throw(_("Error in getting LLM: {0}").format(str(e)))
    return llm, doc


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
    def __init__(self, prompt: str = None):
        self.prompt = prompt
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
            if is_next:
                return model['model_name']
        return self.model_info[0]['model_name']
    
    def get_llm_response(self, prompt: str, model_name: str = None) -> str:
        try:
            so_llm = self.get_structured_output_llm(model_name=model_name)
            ai_msg = so_llm.invoke(prompt)
            return ai_msg.response
        except ResourceExhausted as e:
            frappe.log_error(frappe.get_traceback(), f"RPM limit reached {self.current_model} in NextAILLM.get_llm_response")
            if self.nextai_settings.auto_switch_model_on_rpm:
                self.current_model = self.get_next_model(self.current_model)
                if self.current_model == self.nextai_settings.model_name:
                    frappe.log_error(frappe.get_traceback(), "RPM limit reached for all models in NextAILLM.get_llm_response")
                    frappe.throw(_("RPM limit reached for all the models. Please try again later. Or Please upgrade your plan."))
                return self.get_structured_output_llm(model_name=self.current_model)
            else:
                frappe.throw(_(f"RPM limit reached for the current model {self.current_model}. Please try again later."))