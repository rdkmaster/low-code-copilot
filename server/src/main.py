import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import dspy
import uuid
import json
from intent_schemas import INTENT_SCHEMAS

# --- Basic Setup ---
app = FastAPI()

# CORS (Cross-Origin Resource Sharing) configuration
# Allows the frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-Memory Storage ---
# In a real application, you would use a database or a persistent cache like Redis.
conversation_states = {}
# This represents the page structure, the "single source of truth" on the backend.
# The backend modifies this schema and sends patches to the frontend.
page_schema = {
    "pageId": "page_001",
    "title": "首页",
    "components": []
}

# --- DSPy Configuration ---
# This would be configured with your actual LLM provider (e.g., OpenAI, Anthropic)
# For this example, we'll use a Turbo mock.
turbo = dspy.OpenAI(model='gpt-3.5-turbo', max_tokens=4000)
dspy.settings.configure(lm=turbo)

class InitialIntentSignature(dspy.Signature):
    """Determine the user's primary intent and extract all possible entities from their initial request."""
    user_request: str = dspy.InputField(desc="The user's initial request.")
    intent: str = dspy.OutputField(desc="The single most likely intent. Must be one of: createComponent, updateProperty, unknown.")
    entities: str = dspy.OutputField(desc="A JSON string containing all extracted entities. For example: {\"componentType\": \"Button\", \"text\": \"Login\", \"color\": \"blue\"}")

class ExtractEntitySignature(dspy.Signature):
    """Given a question and a user's answer, extract the specific value for the requested entity."""
    question: str = dspy.InputField(desc="The question that was asked to the user.")
    user_answer: str = dspy.InputField(desc="The user's answer to the question.")
    extracted_value: str = dspy.OutputField(desc="The extracted value for the entity.")

# --- Action Handlers & Patch Generation ---

def find_component_path(schema, component_id):
    """Finds the JSON path to a component in the schema."""
    for i, component in enumerate(schema.get("components", [])):
        if component.get("id") == component_id:
            return f"/components/{i}"
    return None

def handle_create_component(entities):
    """Generates a JSON Patch to create a new component."""
    global page_schema
    
    new_id = str(uuid.uuid4())[:8]
    component_type = entities.get("componentType", "div") # Default to div if not specified
    
    new_component = {
        "id": new_id,
        "type": component_type,
        "props": {}
    }
    if "text" in entities:
        new_component["props"]["text"] = entities["text"]
    if "color" in entities:
        new_component["props"]["color"] = entities["color"]
        
    # The path '-' means append to the end of the array
    path = "/components/-"
    patch = [{"op": "add", "path": path, "value": new_component}]
    
    # Update backend's source of truth
    page_schema["components"].append(new_component)
    
    return patch

def handle_update_property(entities):
    """Generates a JSON Patch to update a component's property."""
    global page_schema
    
    component_id = entities.get("componentId")
    prop_name = entities.get("propertyName")
    prop_value = entities.get("propertyValue")
    
    path_prefix = find_component_path(page_schema, component_id)
    if not path_prefix:
        return [{"error": "Component not found"}]
        
    path = f"{path_prefix}/props/{prop_name}"
    patch = [{"op": "replace", "path": path, "value": prop_value}]
    
    # Update backend's source of truth
    # This is a simplified way; a robust solution would use a JSON Patch library
    component_index = int(path_prefix.split('/')[-1])
    page_schema["components"][component_index]["props"][prop_name] = prop_value
    
    return patch

ACTION_HANDLERS = {
    "createComponent": handle_create_component,
    "updateProperty": handle_update_property
}

# --- API Endpoint ---

class ChatRequest(BaseModel):
    message: str
    sessionId: str

@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.sessionId
    user_message = request.message
    
    # Step 1: Check for an active conversation
    if session_id in conversation_states:
        state = conversation_states[session_id]
        intent_schema = INTENT_SCHEMAS[state["activeIntent"]]
        
        # This is an answer to a follow-up question
        missing_key = state["missingEntities"][0]
        question = intent_schema["params"][missing_key]["prompt"]
        
        # Use DSPy to extract the value from the answer
        extractor = dspy.Predict(ExtractEntitySignature)
        response = extractor(question=question, user_answer=user_message)
        extracted_value = response.extracted_value
        
        # Update state
        state["collectedEntities"][missing_key] = extracted_value
        state["missingEntities"].pop(0)
        
    else:
        # This is a new conversation
        predictor = dspy.Predict(InitialIntentSignature)
        response = predictor(user_request=user_message)
        intent = response.intent
        
        if intent not in INTENT_SCHEMAS:
            return {"message": "I'm sorry, I'm not sure how to help with that."}
            
        intent_schema = INTENT_SCHEMAS[intent]
        
        try:
            entities = json.loads(response.entities)
        except json.JSONDecodeError:
            entities = {}

        # Create a new state
        state = {
            "activeIntent": intent,
            "collectedEntities": entities,
            "missingEntities": []
        }
        
        # Check for missing required entities
        for key, details in intent_schema["params"].items():
            if details["required"] and key not in state["collectedEntities"]:
                state["missingEntities"].append(key)
        
        conversation_states[session_id] = state

    # Step 2: Check if the conversation is complete
    if not state["missingEntities"]:
        # All required entities are collected, execute the action
        handler = ACTION_HANDLERS.get(state["activeIntent"])
        if not handler:
            return {"message": "Error: Action handler not found."}
            
        json_patch = handler(state["collectedEntities"])
        
        # Clean up the completed conversation
        del conversation_states[session_id]
        
        return {"patch": json_patch}
    else:
        # Still need more information, ask the next question
        next_missing_key = state["missingEntities"][0]
        prompt = intent_schema["params"][next_missing_key]["prompt"]
        return {"message": prompt}

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)