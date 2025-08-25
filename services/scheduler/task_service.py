"""
Task Service for Task Management

This module provides the business logic for task CRUD operations,
integrating with the Scheduler Service for task scheduling.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from models.task_models import Task, TaskType, RepeatInterval
from .scheduler_service import SchedulerService
from utils.logger import get_logger


class TaskService:
    """
    Service for managing task CRUD operations
    
    Handles task creation, reading, updating, and deletion,
    while coordinating with the Scheduler Service for scheduling.
    """
    
    def __init__(self, scheduler_service: SchedulerService):
        """
        Initialize the task service
        
        Args:
            scheduler_service: Service for scheduling and managing tasks
        """
        self.scheduler_service = scheduler_service
        self.logger = get_logger(__name__)
        # In-memory storage for now, will be replaced with database later
        self._tasks: Dict[str, Task] = {}

    async def create_task(self, task: Task) -> Task:
        """
        Create a new scheduled or repeated task
        
        Args:
            task: Task to create
            
        Returns:
            Created task with generated ID
            
        Raises:
            ValueError: If task data is invalid
        """
        self._validate_task(task)
        
        if not task.id:
            task.id = str(uuid.uuid4())
        
        task.created_at = datetime.now()
        task.updated_at = datetime.now()
        self._tasks[task.id] = task
        self.logger.info(f"Task '{task.name}' (ID: {task.id}) created and stored")
        
        if task.is_active:
            await self.scheduler_service.schedule_task(task)
            self.logger.info(f"Task '{task.name}' (ID: {task.id}) scheduled")
        
        return task

    async def get_tasks(self, 
                        task_type: Optional[TaskType] = None,
                        is_active: Optional[bool] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[Task]:
        """
        Get list of tasks with optional filtering
        
        Args:
            task_type: Filter by task type
            is_active: Filter by active status
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
            
        Returns:
            List of matching tasks
        """
        tasks = list(self._tasks.values())
        
        # Filters
        if task_type is not None:
            tasks = [t for t in tasks if t.task_type == task_type]
        if is_active is not None:
            tasks = [t for t in tasks if t.is_active == is_active]
        
        # Pagination
        tasks = tasks[offset:offset + limit]
        
        return tasks

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a specific task by ID
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            Task if found, None otherwise
        """
        return self._tasks.get(task_id)

    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Task]:
        """
        Update an existing task
        
        Args:
            task_id: ID of the task to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated task if successful, None if task not found
            
        Raises:
            ValueError: If update data is invalid
        """
        task = self._tasks.get(task_id)
        if not task:
            return None
        
        self._validate_task_updates(updates)
        
        for field, value in updates.items():
            if hasattr(task, field) and field not in ['id', 'created_at']:
                setattr(task, field, value)
        
        
        task.updated_at = datetime.now()
        if 'scheduled_at' in updates or 'repeat_interval' in updates or 'cron_expression' in updates:
            await self.scheduler_service.cancel_task(task_id)
            
            if task.is_active:
                await self.scheduler_service.schedule_task(task)
        
        if 'is_active' in updates:
            if task.is_active:
                await self.scheduler_service.schedule_task(task)
            else:
                await self.scheduler_service.cancel_task(task_id)
        
        return task

    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task and cancel all related jobs
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            True if task was deleted successfully, False otherwise
        """
        if task_id not in self._tasks:
            return False
        
        await self.scheduler_service.cancel_task(task_id)
        del self._tasks[task_id]
        
        return True

    async def pause_task(self, task_id: str) -> bool:
        """
        Pause a task
        
        Args:
            task_id: ID of the task to pause
            
        Returns:
            True if task was paused successfully, False otherwise
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.is_active = False
        task.updated_at = datetime.now()
        
        return await self.scheduler_service.pause_task(task_id)

    async def resume_task(self, task_id: str) -> bool:
        """
        Resume a paused task
        
        Args:
            task_id: ID of the task to resume
            
        Returns:
            True if task was resumed successfully, False otherwise
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.is_active = True
        task.updated_at = datetime.now()
        
        return await self.scheduler_service.resume_task(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task (remove from scheduler but keep in storage)
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was cancelled successfully, False otherwise
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.is_active = False
        task.updated_at = datetime.now()
        
        return await self.scheduler_service.cancel_task(task_id)

    def get_task_count(self, task_type: Optional[TaskType] = None, is_active: Optional[bool] = None) -> int:
        """
        Get count of tasks with optional filtering
        
        Args:
            task_type: Filter by task type
            is_active: Filter by active status
            
        Returns:
            Number of matching tasks
        """
        tasks = list(self._tasks.values())
        
        if task_type is not None:
            tasks = [t for t in tasks if t.task_type == task_type]   
        if is_active is not None:
            tasks = [t for t in tasks if t.is_active == is_active]
        
        return len(tasks)

    def _validate_task(self, task: Task):
        """
        Validate task data
        
        Args:
            task: Task to validate
            
        Raises:
            ValueError: If task data is invalid
        """
        if not task.name:
            raise ValueError("Task name is required")
        
        if not task.task_type:
            raise ValueError("Task type is required")
        
        if not task.scheduled_at:
            raise ValueError("Scheduled time is required")
        
        if task.task_type == TaskType.REPEATED:
            if not task.repeat_interval:
                raise ValueError("Repeat interval is required for recurring tasks")
            
            if task.repeat_interval == RepeatInterval.CUSTOM and not task.cron_expression:
                raise ValueError("Cron expression is required for custom repeat intervals")
        
        # Validate scheduled time is in the future for one-time tasks
        if task.task_type == TaskType.SCHEDULED and task.scheduled_at <= datetime.now():
            raise ValueError("Scheduled time must be in the future for one-time tasks")

    def _validate_task_updates(self, updates: Dict[str, Any]):
        """
        Validate task update data
        
        Args:
            updates: Update data to validate
            
        Raises:
            ValueError: If update data is invalid
        """
        if 'scheduled_at' in updates:
            scheduled_at = updates['scheduled_at']
            if isinstance(scheduled_at, str):
                scheduled_at = datetime.fromisoformat(scheduled_at)
            
            # For one-time tasks, ensure scheduled time is in the future
            if updates.get('task_type') == TaskType.SCHEDULED or 'task_type' not in updates:
                if scheduled_at <= datetime.now():
                    raise ValueError("Scheduled time must be in the future for one-time tasks")
        
        if 'repeat_interval' in updates:
            repeat_interval = updates['repeat_interval']
            if repeat_interval == RepeatInterval.CUSTOM and not updates.get('cron_expression'):
                raise ValueError("Cron expression is required for custom repeat intervals")
