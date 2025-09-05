from fastapi import FastAPI
import importlib.metadata
from services import (
    supervisor_router,
    planning_router,
    knowledge_router,
    habit_router,
    notification_router
)
from api.routes.messaging import messaging_router
from api.routes.tasks import tasks_router
from utils.logging_config import setup_logging
from utils.config import get_settings

app = FastAPI(title="Assistant Octopus API")

@app.on_event("startup")
async def startup_event():
    """Initialize logging and other startup tasks."""
    try:
        settings = get_settings()
        setup_logging(
            log_level=settings.log_level,
            log_file=settings.log_file,
            log_dir=settings.log_dir,
            max_bytes=settings.log_max_bytes,
            backup_count=settings.log_backup_count,
            console_output=settings.log_console_output
        )
    except Exception as e:
        # Fallback to basic logging if configuration fails
        import logging
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Failed to initialize logging configuration: {e}")

@app.get("/health")
async def health_check():
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Health check endpoint called")
    return {"status": "ok"}

@app.get("/status")
async def status_check():
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Status check endpoint called")
    return {"status": "running", "version": importlib.metadata.version("assistant-octopus")}

app.include_router(supervisor_router)
app.include_router(planning_router)
app.include_router(knowledge_router)
app.include_router(habit_router)
app.include_router(notification_router)
app.include_router(messaging_router)
app.include_router(tasks_router)