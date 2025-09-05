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
    """Initialize logging, services and other startup tasks."""
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
        
        # Initialize services for the FastAPI app
        from services.service_registry import service_registry
        from services.messaging.factory import MessagingServiceFactory
        from services.scheduler import SchedulerService, TaskService
        from db.repositories.task_repo import TaskRepo
        from db.storage import get_storage_backend
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info("Initializing services...")
        
        # Initialize storage backend first
        storage_backend = get_storage_backend()
        service_registry.set_storage_backend(storage_backend)
        logger.info("Storage backend initialized")
        
        # Initialize messaging service
        messaging_service = await MessagingServiceFactory.initialize_service()
        service_registry.set_messaging_service(messaging_service)
        logger.info("Messaging service initialized")
        
        # Initialize scheduler service
        scheduler_service = SchedulerService(messaging_service)
        await scheduler_service.start()
        service_registry.set_scheduler_service(scheduler_service)
        logger.info("Scheduler service initialized")
        
        # Initialize task repository
        task_repo = TaskRepo(storage_backend)
        service_registry.set_task_repo(task_repo)
        logger.info("Task repository initialized")
        
        # Initialize task service with both scheduler and repository
        task_service = TaskService(scheduler_service, task_repo)
        service_registry.set_task_service(task_service)
        logger.info("Task service initialized")
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        # Fallback to basic logging if configuration fails
        import logging
        logging.basicConfig(level=logging.INFO)
        logging.error(f"Failed to initialize application: {e}")
        raise

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