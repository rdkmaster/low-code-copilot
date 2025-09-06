import dspy
import litellm
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .custom_lm import CustomLM
from .observation_tools import get_page_outline, get_component_details, find_components
from .page_state import get_current_page_schema
from .planner import Planner

# Initialize the FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]
) 

# Configure DSPy and LiteLLM
# 注意：为了让代码正常工作，我使用了其他文件中看到的示例key。
# 在生产环境中，请务必使用环境变量等安全方式管理API Key。
lm = CustomLM(
    api_base="https://xiaoai.plus/v1",
    api_key="sk-yhJhB5JgplmHZHXghuCbAbxr3GUzotlKd4MffZedhxVVNAZX"
)
dspy.settings.configure(lm=lm)

# --- Pydantic Models for API ---
class ChatRequest(BaseModel):
    prompt: str

# --- DSPy Signature for Querying (for single-step) ---
class QuerySignature(dspy.Signature):
    """Given the user prompt and context, answer the user's question."""
    context = dspy.InputField(desc="JSON data about the current page state")
    question = dspy.InputField(desc="The user's original question")
    answer = dspy.OutputField(desc="A natural language answer to the user's question")

# --- Core Logic ---

query_predictor = dspy.Predict(QuerySignature)

def handle_query_intent(prompt: str):
    """Handles intents that are about querying the page state."""
    # 简单的启发式方法来选择工具
    context_data = None
    if "how many" in prompt or "find" in prompt or "all" in prompt:
        filters = [] 
        context_data = find_components(filters=filters)
    elif "details" in prompt or "what is" in prompt:
        component_id = "" 
        if component_id:
            context_data = get_component_details(component_id)
    else:
        context_data = get_page_outline()

    if not context_data:
        return "抱歉，我找不到可以回答您问题的信息。"

    # 让LLM整合答案
    result = query_predictor(context=str(context_data), question=prompt)
    return result.answer

def route_request(user_query: str) -> str:
    """
    判断用户请求是“简单指令”还是“复杂目标”。
    """
    prompt = f"""
请判断以下用户请求，更像是一个可以通过单一步骤完成的“简单指令”，还是一个需要多个步骤才能完成的“复杂目标”。
请只回答 'single' 或 'multi'。

用户请求: "{user_query}"
"""
    
    try:
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=[{"content": prompt, "role": "user"}],
            max_tokens=5,
            temperature=0.0
        )
        result = response.choices[0].message.content.strip().lower()
        
        if "multi" in result:
            return "multi"
        else:
            return "single"
            
    except Exception as e:
        print(f"调用LLM进行路由时出错: {e}")
        return "single"

@app.post("/chat")
def chat(req: ChatRequest):
    prompt = req.prompt

    # 1. 使用新的分流器判断用户意图
    request_type = route_request(prompt)

    # 2. 根据意图类型进行路由
    if request_type == 'multi':
        # 如果是复杂目标，则启动规划器
        print("请求被分类为 'multi'，启动规划器...")
        planner = Planner()
        page_state = get_current_page_schema()
        generated_plan = planner.generate_plan(prompt, page_state)
        
        if generated_plan:
            return {"type": "plan", "data": generated_plan}
        else:
            return {"type": "error", "data": "抱歉，我无法为您生成行动计划。"}

    else: # request_type == 'single'
        # 如果是简单指令，可以沿用旧的逻辑（或进一步细分）
        # 这里我们暂时假定所有 single 请求都是查询
        print("请求被分类为 'single'，执行查询...")
        response_text = handle_query_intent(prompt)
        return {"type": "text", "data": response_text}

@app.options("/chat")
def options_chat():
    return {}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)