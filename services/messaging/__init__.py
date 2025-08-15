"""
Messaging Service Package

Handles asynchronous task processing, job queuing, and worker pool management.
"""

from .models import Job, Message, JobStatus, JobPriority
from .job_queue import JobQueue, InMemoryJobQueue
from .messaging_service import MessagingService
from .router import messaging_router
from .factory import (
    MessagingServiceFactory,
    get_messaging_service,
    initialize_messaging_service,
    shutdown_messaging_service
)

__all__ = [
    "JobQueue", 
    "InMemoryJobQueue",
    "Job",
    "Message", 
    "JobStatus",
    "JobPriority",
    "MessagingService",
    "messaging_router",
    "MessagingServiceFactory",
    "get_messaging_service",
    "initialize_messaging_service",
    "shutdown_messaging_service"
]
