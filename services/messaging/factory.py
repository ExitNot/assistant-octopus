"""
Messaging Service Factory

Manages the creation and lifecycle of messaging service components,
providing a centralized way to initialize and configure the service.
"""

from typing import Optional
from .job_queue import InMemoryJobQueue
from .messaging_service import MessagingService
from utils.config import get_settings


class MessagingServiceFactory:
    """
    Factory for creating and managing messaging service instances
    
    Handles:
    - Service initialization with proper configuration
    - Dependency injection
    - Service lifecycle management
    """
    
    _instance: Optional[MessagingService] = None
    _job_queue: Optional[InMemoryJobQueue] = None
    
    @classmethod
    def create_job_queue(cls) -> InMemoryJobQueue:
        """Create a configured job queue instance"""
        settings = get_settings()
        
        return InMemoryJobQueue(
            backup_file=settings.messaging_backup_file
        )
    
    @classmethod
    def create_messaging_service(cls) -> MessagingService:
        """Create a configured messaging service instance"""
        if cls._instance is None:
            # Create job queue if not exists
            if cls._job_queue is None:
                cls._job_queue = cls.create_job_queue()
            
            # Create messaging service
            cls._instance = MessagingService(cls._job_queue)
        
        return cls._instance
    
    @classmethod
    def get_messaging_service(cls) -> MessagingService:
        """Get the singleton messaging service instance"""
        if cls._instance is None:
            cls._instance = cls.create_messaging_service()
        
        return cls._instance
    
    @classmethod
    async def initialize_service(cls) -> MessagingService:
        """Initialize and start the messaging service"""
        service = cls.get_messaging_service()
        await service.start()
        return service
    
    @classmethod
    async def shutdown_service(cls):
        """Shutdown the messaging service gracefully"""
        if cls._instance:
            await cls._instance.stop()
            cls._instance = None
        
        if cls._job_queue:
            cls._job_queue = None
    
    @classmethod
    def reset(cls):
        """Reset the factory (useful for testing)"""
        cls._instance = None
        cls._job_queue = None


# Convenience functions
def get_messaging_service() -> MessagingService:
    """Get the messaging service instance"""
    return MessagingServiceFactory.get_messaging_service()


async def initialize_messaging_service() -> MessagingService:
    """Initialize and start the messaging service"""
    return await MessagingServiceFactory.initialize_service()


async def shutdown_messaging_service():
    """Shutdown the messaging service"""
    await MessagingServiceFactory.shutdown_service()
