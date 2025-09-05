"""
Service Registry for Dependency Injection

Provides a centralized registry for sharing service instances
between the CLI server and FastAPI application.
"""

from typing import Optional
from services.messaging.messaging_service import MessagingService
from services.scheduler.scheduler_service import SchedulerService
from services.scheduler.task_service import TaskService
from db.repositories.task_repo import TaskRepo
from db.storage import StorageBackend


class ServiceRegistry:
    """Singleton registry for service instances"""
    
    _instance: Optional['ServiceRegistry'] = None
    _messaging_service: Optional[MessagingService] = None
    _scheduler_service: Optional[SchedulerService] = None
    _task_service: Optional[TaskService] = None
    _task_repo: Optional[TaskRepo] = None
    _storage_backend: Optional[StorageBackend] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def set_messaging_service(self, service: MessagingService):
        """Set the messaging service instance"""
        self._messaging_service = service
    
    def set_scheduler_service(self, service: SchedulerService):
        """Set the scheduler service instance"""
        self._scheduler_service = service
    
    def set_task_service(self, service: TaskService):
        """Set the task service instance"""
        self._task_service = service
    
    def set_task_repo(self, repo: TaskRepo):
        """Set the task repository instance"""
        self._task_repo = repo
    
    def set_storage_backend(self, backend: StorageBackend):
        """Set the storage backend instance"""
        self._storage_backend = backend
    
    def get_messaging_service(self) -> Optional[MessagingService]:
        """Get the messaging service instance"""
        return self._messaging_service
    
    def get_scheduler_service(self) -> Optional[SchedulerService]:
        """Get the scheduler service instance"""
        return self._scheduler_service
    
    def get_task_service(self) -> Optional[TaskService]:
        """Get the task service instance"""
        return self._task_service
    
    def get_task_repo(self) -> Optional[TaskRepo]:
        """Get the task repository instance"""
        return self._task_repo
    
    def get_storage_backend(self) -> Optional[StorageBackend]:
        """Get the storage backend instance"""
        return self._storage_backend
    
    def is_initialized(self) -> bool:
        """Check if all services are initialized"""
        return all([
            self._messaging_service is not None,
            self._scheduler_service is not None,
            self._task_service is not None,
            self._task_repo is not None,
            self._storage_backend is not None
        ])
    
    def clear(self):
        """Clear all registered services (useful for testing)"""
        self._messaging_service = None
        self._scheduler_service = None
        self._task_service = None
        self._task_repo = None
        self._storage_backend = None


# Global registry instance
service_registry = ServiceRegistry()
