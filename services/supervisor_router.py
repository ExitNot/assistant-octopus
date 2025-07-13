from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from services.ollama_llm import OllamaClient, OllamaAPIError
from typing import Optional, Dict

# In-memory conversation store (for MVP, not production)
_conversations: Dict[str, list] = {}

class SupervisorPromptRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class SupervisorPromptResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

supervisor_router = APIRouter(prefix="/supervisor", tags=["Supervisor"])

@supervisor_router.post("/execute", response_model=SupervisorPromptResponse)
async def supervisor_execute(
    req: SupervisorPromptRequest,
    request: Request,
):
    session_id = req.session_id
    user_id = req.user_id
    conversation_key = f"{user_id}:{session_id}"
    conversation = _conversations.setdefault(conversation_key, [])
    conversation.append({"role": "user", "content": req.prompt})
    ollama = OllamaClient()
    try:
        response = await ollama.generate(prompt=req.prompt)
    except OllamaAPIError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    conversation.append({"role": "assistant", "content": response})
    return SupervisorPromptResponse(response=response, session_id=session_id, user_id=user_id) 