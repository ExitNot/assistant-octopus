from fastapi import FastAPI
import importlib.metadata
from services import (
    supervisor_router,
    planning_router,
    knowledge_router,
    habit_router,
    notification_router,
)

app = FastAPI(title="Assistant Octopus API")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/status")
async def status_check():
    return {"status": "running", "version": importlib.metadata.version("assistant-octopus")}

app.include_router(supervisor_router)
app.include_router(planning_router)
app.include_router(knowledge_router)
app.include_router(habit_router)
app.include_router(notification_router) 