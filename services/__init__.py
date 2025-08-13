from fastapi import APIRouter, HTTPException, status
from .supervisor import supervisor_router
from .llm import OllamaClient

planning_router = APIRouter(prefix="/planning", tags=["Planning"])
knowledge_router = APIRouter(prefix="/knowledge", tags=["Knowledge"])
habit_router = APIRouter(prefix="/habit", tags=["Habit Tracker"])
notification_router = APIRouter(prefix="/notification", tags=["Notification"])

# Planning endpoints
@planning_router.post("/tasks/create")
async def create_task():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@planning_router.get("/tasks/list")
async def list_tasks():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@planning_router.put("/tasks/{task_id}/update")
async def update_task(task_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@planning_router.get("/calendar/events")
async def get_calendar_events():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

# Knowledge endpoints
@knowledge_router.get("/search")
async def search_knowledge():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@knowledge_router.post("/notes/create")
async def create_note():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@knowledge_router.put("/notes/{note_id}/update")
async def update_note(note_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

# Habit Tracker endpoints
@habit_router.post("/habits/log")
async def log_habit():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@habit_router.get("/habits/stats")
async def habit_stats():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@habit_router.put("/habits/{habit_id}/update")
async def update_habit(habit_id: str):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

# Notification endpoints
@notification_router.post("/notifications/schedule")
async def schedule_notification():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@notification_router.get("/notifications/list")
async def list_notifications():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented") 