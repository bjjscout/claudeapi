import os
import asyncio
import httpx
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage, TextBlock

if "ANTHROPIC_API_KEY" in os.environ:
    del os.environ["ANTHROPIC_API_KEY"]

app = FastAPI(title="Claude Max Personal API")
API_KEY = "jiujitsu2020"
MAX_CONCURRENT = 6
_semaphore = asyncio.Semaphore(MAX_CONCURRENT)
_alert_sent = False  # Avoid spamming the webhook

async def notify_claude_down(error: str):
    global _alert_sent
    if _alert_sent:
        return
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://n8n.jeffrey-epstein.com/webhook/claudedown",
                json={"error": error, "message": "Claude API is down - re-authentication required"},
                timeout=10
            )
        _alert_sent = True
        print(f"ALERT SENT: Claude down webhook triggered")
    except Exception as e:
        print(f"Failed to send webhook: {e}")

async def check_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/health")
async def health():
    return {"status": "running"}

class Message(BaseModel):
    role: str
    content: str

class GenRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = "You are a professional content writer."
    model: Optional[str] = None
    conversation_history: Optional[List[Message]] = []

class GenResponse(BaseModel):
    result: str
    model_used: str

@app.post("/generate", response_model=GenResponse)
async def generate(req: GenRequest, x_api_key: str = Header(None)):
    global _alert_sent
    await check_key(x_api_key)
    full_prompt = ""
    if req.conversation_history:
        for msg in req.conversation_history:
            if msg.role == "user":
                full_prompt += f"User: {msg.content}\n\n"
            elif msg.role == "assistant":
                full_prompt += f"Assistant: {msg.content}\n\n"
    full_prompt += f"User: {req.prompt}"
    options = ClaudeAgentOptions(
        system_prompt=req.system_prompt,
        max_turns=5,
        allowed_tools=[]
    )
    if req.model:
        options.model = req.model
    async with _semaphore:
        try:
            text = ""
            model_used = req.model or "default"
            async for msg in query(prompt=full_prompt, options=options):
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            text += block.text
                elif isinstance(msg, ResultMessage) and hasattr(msg, "result") and msg.result:
                    text = msg.result
            if not text:
                raise HTTPException(status_code=500, detail="Empty response")
            _alert_sent = False  # Reset alert flag on success
            print(f"PROMPT: {req.prompt}")
            print(f"RESPONSE: {text}")
            return GenResponse(result=text, model_used=model_used)
        except HTTPException:
            raise
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "expired" in error_str.lower() or "authenticate" in error_str.lower():
                await notify_claude_down(error_str)
            raise HTTPException(status_code=500, detail=error_str)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
