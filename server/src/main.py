import dspy
import litellm
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .custom_lm import CustomLM
from .observation_tools import get_page_outline, get_component_details, find_components
from .page_state import get_current_page_schema
from .planner import Planner
from .execution_engine import ExecutionEngine
from .mcp_tools import tool_registry

# Initialize the FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]
) 

# Configure DSPy and LiteLLM
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
    request_type = route_request(prompt)

    if request_type == 'multi':
        print("请求被分类为 'multi'，启动规划和执行流程...")
        try:
            # 1. 规划
            planner = Planner()
            page_state = get_current_page_schema()
            generated_plan = planner.generate_plan(prompt, page_state)
            if not generated_plan:
                raise HTTPException(status_code=500, detail="无法生成行动计划。")

            # 2. 执行
            engine = ExecutionEngine(tool_registry)
            execution_results = engine.execute_plan(generated_plan)
            
            # 3. 返回成功响应
            return {"type": "execution_success", "data": execution_results}

        except Exception as e:
            print(f"处理复杂请求时出错: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    else: # request_type == 'single'
        print("请求被分类为 'single'，执行查询...")
        try:
            response_text = handle_query_intent(prompt)
            return {"type": "text", "data": response_text}
        except Exception as e:
            print(f"处理简单请求时出错: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.options("/chat")
def options_chat():
    return {}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
