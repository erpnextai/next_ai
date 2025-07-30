# NextAI - Frappe Custom App

## Summary
**NextAI** is a custom Frappe app that integrates with **Gemini LLM models** to enhance content creation using AI. It enables features such as:
- Generating **Terms and Conditions** or similar content directly within text editor fields.
- **Correcting grammar**.
- **Enhancing existing content** intelligently based on prompts.

## Version Support
NextAI supports the following Frappe versions:
- **Version 14**
- **Version 15**

## How To Use?
1. Navigate to any text editor field where AI content is needed.
2. You will see a button labeled **"NextAI"**.
3. Enter your **prompt** in the field (e.g., "Generate privacy policy").
4. Click the **NextAI** button.
5. The AI-generated content will be inserted into the field based on your prompt.

![WhatsApp Image 2025-06-24 at 9 19 28 PM](https://github.com/user-attachments/assets/6ea75a79-5ca2-4650-bed7-2d1ed151e04e)


## How to Set Up:

* [How to configure the app? - Video](https://www.erpnextai.in/video)
* [How to setup?](next_ai/docs/how-to-setup.md)

1. There are two main doctypes you need to review:

   * **`NextAI Model Info`** – The data for this doctype is fetched from fixtures. You simply need to run the migration.
   * **`NextAI Settings`** – In this doctype, please configure your API key, select the appropriate model, and choose the platform. The process is straightforward and user-friendly.

2. Once the setup is complete, please ensure that the user has either the **`System Manager`** or **`NextAI User`** role. Only users with these roles will be able to access this feature.



Here's a more polite and professional version of your content:

---

### Supported Field Types

NextAI currently supports the following field types:

* **Markdown Editor**
* **Small Text**
* **Long Text**
* **HTML Editor**
* **Text Editor**
* **Code**

---

### Need Assistance?

If you have any questions or require support, please feel free to raise a ticket using the link below. Our team will be happy to assist you.

👉 [NextAI Support Ticket](https://www.erpnextai.in/support)


## Future Updates

- Currently, we support **Gemini**. In future releases, we plan to add support for **ChatGPT** and **GROQ**.
- We are also planning to introduce **AI-enhanced personal chat** within the system.

