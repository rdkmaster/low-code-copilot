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

def summarize_page_state(page_state: dict) -> str:
    """
    将完整的页面状态JSON，转换为对LLM友好的Markdown格式摘要。

    :param page_state: 代表页面当前状态的JSON对象。
    :return: Markdown格式的字符串摘要。
    """
    if not page_state or not page_state.get('children'):
        return "当前页面为空。"

    summary_lines = []

    def _summarize_recursive(component: dict, indent_level: int):
        """递归辅助函数，用于生成每个组件的摘要行。"""
        indent = "  " * indent_level
        component_type = component.get("type", "Unknown")
        component_id = component.get("id", "no-id")
        
        summary_lines.append(f"{indent}- {component_type} (id: {component_id})")

        if "children" in component and isinstance(component["children"], list):
            for child in component["children"]:
                _summarize_recursive(child, indent_level + 1)

    # 从根节点开始递归
    _summarize_recursive(page_state, 0)
    
    return "\n".join(summary_lines)