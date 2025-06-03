import frappe


@frappe.whitelist(allow_guest=True)
def get_field_info(**kwargs):
    return {"status": "success"}


@frappe.whitelist(allow_guest=True)
def test_gemini(**kwargs):
    import os

    if "GOOGLE_API_KEY" not in os.environ:
        return {"status": "error", "message": "GOOGLE_API_KEY not set in environment variables"}
    
    from langchain_google_genai import ChatGoogleGenerativeAI

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
            "You are a helpful assistant that translates English to French. Translate the user sentence.",
        ),
        ("human", "I love programming."),
    ]
    ai_msg = llm.invoke(messages)
    ai_msg
    return {"status": "success", "message": ai_msg.content}
