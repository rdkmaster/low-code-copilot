
import dspy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .custom_lm import CustomLM
from .observation_tools import get_page_outline, get_component_details, find_components

# Initialize the FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"]
) 

# Configure DSPy
llm = CustomLM()
dspy.settings.configure(lm=llm)

# --- Pydantic Models for API ---
class ChatRequest(BaseModel):
    prompt: str

# --- DSPy Signatures for Triage and Query ---
class TriageSignature(dspy.Signature):
    """Classify the user's intent as either 'query_state' or 'modify_state'"""
    user_prompt = dspy.InputField(desc="The user's request")
    intent = dspy.OutputField(desc="Must be either 'query_state' or 'modify_state'")

class QuerySignature(dspy.Signature):
    """Given the user prompt and context, answer the user's question."""
    context = dspy.InputField(desc="JSON data about the current page state")
    question = dspy.InputField(desc="The user's original question")
    answer = dspy.OutputField(desc="A natural language answer to the user's question")

# --- Core Logic ---

triage_predictor = dspy.Predict(TriageSignature)
query_predictor = dspy.Predict(QuerySignature)

def handle_query_intent(prompt: str):
    """Handles intents that are about querying the page state."""
    # For simplicity, we'll use a basic heuristic to choose a tool.
    # A more advanced implementation would use another LLM call to select the tool.
    
    context_data = None
    if "how many" in prompt or "find" in prompt or "all" in prompt:
        # A simple filter based on prompt keywords
        # This is a placeholder for a more sophisticated filter logic
        filters = [] # In a real scenario, we'd extract filters from the prompt
        context_data = find_components(filters=filters)
    elif "details" in prompt or "what is" in prompt:
        # This is a placeholder for extracting a component ID
        component_id = "" # In a real scenario, we'd extract this
        if component_id:
            context_data = get_component_details(component_id)
    else:
        context_data = get_page_outline()

    if not context_data:
        return "I'm sorry, I couldn't find any information to answer your question."

    # Ask the LLM to synthesize an answer
    result = query_predictor(context=str(context_data), question=prompt)
    return result.answer

@app.post("/chat")
def chat(req: Chat.Request):
    prompt = req.prompt

    # 1. Triage the user's intent
    triage_result = triage_predictor(user_prompt=prompt)
    intent = triage_result.intent

    # 2. Route based on intent
    if intent == 'query_state':
        response_text = handle_query_intent(prompt)
        return {"text": response_text}
    else: # intent == 'modify_state'
        # Placeholder for the modification logic from previous lectures
        # This is where multi-turn dialog, fact-checking, and JSON patch generation would go.
        return {"text": f"This would be a modification. (Original prompt: {prompt})"}

@app.options("/chat")
def options_chat():
    return {}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
