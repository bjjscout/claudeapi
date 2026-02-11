import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage, TextBlock

if "ANTHROPIC_API_KEY" in os.environ:
    del os.environ["ANTHROPIC_API_KEY"]

app = FastAPI(title="Claude Max Personal API")
API_KEY = "jiujitsu2020"

async def check_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/health")
async def health():
    return {"status": "running"}

class GenRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = "You are a professional content writer."
    model: Optional[str] = None

class GenResponse(BaseModel):
    result: str
    model_used: str

@app.post("/generate", response_model=GenResponse)
async def generate(req: GenRequest, x_api_key: str = Header(None)):
    await check_key(x_api_key)
    try:
        text = ""
        model_used = req.model or "default"
        
        # Create ClaudeAgentOptions with the correct parameters
        options = ClaudeAgentOptions(
            system_prompt=req.system_prompt,
            max_turns=1,
            allowed_tools=[]
        )
        
        if req.model:
            options.model = req.model
            
        async for msg in query(prompt=req.prompt, options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        text += block.text
            elif isinstance(msg, ResultMessage) and hasattr(msg, "result") and msg.result:
                text = msg.result
        
        if not text:
            raise HTTPException(status_code=500, detail="Empty response")
        return GenResponse(result=text, model_used=model_used)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
