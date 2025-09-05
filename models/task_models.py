"""
Task Models for Scheduler Service

This module defines the core data structures for the scheduler service,
including task types, repeat intervals, and task representation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid


class TaskType(Enum):
    """Task type enumeration"""
    SCHEDULED = "scheduled"
    REPEATED = "repeated"


class RepeatInterval(Enum):
    """Repeat interval enumeration for recurring tasks"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class Task:
    """
    Task representation for scheduling and execution
    
    Attributes:
        id: Unique identifier for the task
        name: Human-readable name for the task
        description: Optional description of what the task does
        task_type: Type of task (scheduled or repeated)
        payload: Task-specific data and parameters
        scheduled_at: When the task should execute
        repeat_interval: How often to repeat (for recurring tasks)
        cron_expression: Custom cron expression for complex schedules
        is_active: Whether the task is currently active
        created_at: Timestamp when task was created
        updated_at: Timestamp when task was last updated
    """
    id: Optional[str] = None
    name: str = None
    description: Optional[str] = None
    task_type: TaskType = None
    payload: Dict[str, Any] = None
    scheduled_at: datetime = None
    repeat_interval: Optional[RepeatInterval] = None
    cron_expression: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        """Initialize default values after object creation"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.payload is None:
            self.payload = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        data = asdict(self)
        # Convert enum values to their string representations
        if isinstance(data.get('task_type'), TaskType):
            data['task_type'] = data['task_type'].value
        if isinstance(data.get('repeat_interval'), RepeatInterval):
            data['repeat_interval'] = data['repeat_interval'].value
        if isinstance(data.get('scheduled_at'), datetime):
            data['scheduled_at'] = data['scheduled_at'].isoformat()
        if isinstance(data.get('created_at'), datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data.get('updated_at'), datetime):
            data['updated_at'] = data['updated_at'].isoformat()

        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary data"""
        # Convert string representations back to proper types
        if isinstance(data.get('task_type'), str):
            data['task_type'] = TaskType(data['task_type'])
        if isinstance(data.get('repeat_interval'), str):
            data['repeat_interval'] = RepeatInterval(data['repeat_interval'])
        
        # Convert datetime strings back to datetime objects
        for field in ['scheduled_at', 'created_at', 'updated_at']:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def is_recurring(self) -> bool:
        """Check if task is recurring"""
        return self.task_type == TaskType.REPEATED
    
    def is_one_time(self) -> bool:
        """Check if task is one-time scheduled"""
        return self.task_type == TaskType.SCHEDULED
    
    def has_custom_schedule(self) -> bool:
        """Check if task uses custom cron expression"""
        return self.repeat_interval == RepeatInterval.CUSTOM and self.cron_expression is not None
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()
