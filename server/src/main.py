from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
from pydantic import BaseModel
from typing import List, Dict, Any
from starlette.responses import Response

app = FastAPI()

# 更新 CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境建议设置具体的源
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # 明确包含 OPTIONS
    allow_headers=[
        "Content-Type", 
        "Authorization", 
        "Accept", 
        "Origin", 
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["*"],
    max_age=3600,  # preflight 请求的缓存时间
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

async def fetch_chat_completion(messages: List[Dict[str, str]]) -> StreamingResponse:
    url = "https://xiaoai.plus/v1/chat/completions"
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "你是一个大语言模型机器人"
            },
            *messages
        ],
        "stream": True,
        "model": "gpt-3.5-turbo",
        "temperature": 0.5,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "top_p": 1
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-yhJhB5JgplmHZHXghuCbAbxr3GUzotlKd4MffZedhxVVNAZX"
    }

    async def stream_response():
        print("开始流式响应...")
        async with httpx.AsyncClient() as client:
            print(f"发送请求到: {url}")
            print(f"请求负载: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            print(f"请求头: {headers}")
            
            async with client.stream('POST', url, json=payload, headers=headers) as response:
                print(f"收到响应状态码: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"错误响应: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="API request failed")
                
                async for line in response.aiter_lines():
                    print(f"收到数据行: {line}")
                    if line.startswith('data: '):
                        line = line[6:]  # 移除 'data: ' 前缀
                        if line.strip() == '[DONE]':
                            print("收到结束标记 [DONE]")
                            continue
                        try:
                            json_data = json.loads(line)
                            content = json_data['choices'][0]['delta'].get('content', '')
                            if content:
                                print(f"解析到内容: {content}")
                                yield content
                        except json.JSONDecodeError as e:
                            print(f"JSON解析错误: {e}")
                            continue

    return StreamingResponse(stream_response(), media_type="text/plain")

@app.options("/chat")
async def options_chat():
    print("=== 收到 OPTIONS 预检请求 ===")
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
        "Access-Control-Max-Age": "3600",
    }
    print(f"返回 CORS 头部: {json.dumps(headers, indent=2)}")
    
    response = Response(
        status_code=200,
        headers=headers
    )
    print(f"响应状态码: {response.status_code}")
    return response

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print("=== 收到新的聊请求 ===")
    print(f"请求内容: {request}")
    try:
        messages = [msg.dict() for msg in request.messages]
        print(f"处理后的消息: {messages}")
        return await fetch_chat_completion(messages=messages)
    except Exception as e:
        print(f"处理请求时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 添加错误处理中间件
@app.middleware("http")
async def catch_exceptions_middleware(request, call_next):
    try:
        print(f"收到请求: {request.method} {request.url}")
        print(f"请求头: {request.headers}")
        
        # 只有非 OPTIONS 请求才尝试读取和解析请求体
        if request.method == "OPTIONS":
            return await call_next(request)

        body = await request.body()
        try:
            print(f"请求体: {json.loads(body.decode('utf-8'))}")
        except json.JSONDecodeError:
            print(f"请求体解码失败，原始字节: {body}")
        
        return await call_next(request)
    except Exception as e:
        print(f"中间件捕获到错误: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"message": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
