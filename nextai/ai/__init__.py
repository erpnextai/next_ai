import os
import frappe
import time
from langchain_google_genai import ChatGoogleGenerativeAI
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