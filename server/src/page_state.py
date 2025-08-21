
# This file holds the mock state of the low-code editor's page.
# In a real application, this would be managed by a database or a more robust state management system.

def get_current_page_schema():
    """
    Returns the mock page schema. This represents the current state of the UI.
    """
    return {
        "id": "root",
        "type": "Page",
        "props": {},
        "children": [
            {
                "id": "header_123",
                "type": "Header",
                "props": {"title": "My App"},
                "children": [
                    {
                        "id": "logo_789",
                        "type": "Image",
                        "props": {"src": "logo.png", "alt": "logo"}
                    },
                    {
                        "id": "title_456",
                        "type": "Title",
                        "props": {"text": "Welcome", "level": 1}
                    }
                ]
            },
            {
                "id": "form_abc",
                "type": "Form",
                "props": {"name": "login_form"},
                "children": [
                    {
                        "id": "input_email",
                        "type": "Input",
                        "props": {"label": "Email", "placeholder": "Enter your email"}
                    },
                    {
                        "id": "input_password",
                        "type": "Input",
                        "props": {"label": "Password", "type": "password"}
                    },
                    {
                        "id": "btn_login",
                        "type": "Button",
                        "props": {"text": "Login", "color": "blue"}
                    }
                ]
            },
            {
                "id": "footer_xyz",
                "type": "Footer",
                "props": {},
                "children": [
                    {
                        "id": "text_copyright",
                        "type": "Text",
                        "props": {"text": "© 2024 My Company", "fontSize": "small"}
                    }
                ]
            }
        ]
    }
