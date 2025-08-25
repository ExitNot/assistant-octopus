"""
API Models for Task Management

This module defines the request and response models for the task management API,
using Pydantic for validation and serialization.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from models.task_models import TaskType, RepeatInterval


class CreateTaskRequest(BaseModel):
    """Request model for creating a new task"""
    name: str = Field(..., min_length=1, max_length=255, description="Task name")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    task_type: TaskType = Field(..., description="Type of task (scheduled or repeated)")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task-specific data and parameters")
    scheduled_at: datetime = Field(..., description="When the task should execute")
    repeat_interval: Optional[RepeatInterval] = Field(None, description="How often to repeat (for recurring tasks)")
    cron_expression: Optional[str] = Field(None, max_length=100, description="Custom cron expression for complex schedules")


class UpdateTaskRequest(BaseModel):
    """Request model for updating an existing task"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Task name")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    payload: Optional[Dict[str, Any]] = Field(None, description="Task-specific data and parameters")
    scheduled_at: Optional[datetime] = Field(None, description="When the task should execute")
    repeat_interval: Optional[RepeatInterval] = Field(None, description="How often to repeat (for recurring tasks)")
    cron_expression: Optional[str] = Field(None, max_length=100, description="Custom cron expression for complex schedules")
    is_active: Optional[bool] = Field(None, description="Whether the task is currently active")


class TaskResponse(BaseModel):
    """Response model for a single task"""
    id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    task_type: TaskType = Field(..., description="Type of task")
    payload: Dict[str, Any] = Field(..., description="Task-specific data and parameters")
    scheduled_at: datetime = Field(..., description="When the task should execute")
    repeat_interval: Optional[RepeatInterval] = Field(None, description="Repeat interval for recurring tasks")
    cron_expression: Optional[str] = Field(None, description="Custom cron expression")
    is_active: bool = Field(..., description="Whether the task is currently active")
    created_at: datetime = Field(..., description="When the task was created")
    updated_at: datetime = Field(..., description="When the task was last updated")


class TaskListResponse(BaseModel):
    """Response model for a list of tasks"""
    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of tasks per page")


class TaskControlRequest(BaseModel):
    """Request model for task control operations"""
    action: str = Field(..., description="Action to perform (pause, resume, cancel)")


class TaskControlResponse(BaseModel):
    """Response model for task control operations"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Result message")
    task_id: str = Field(..., description="ID of the affected task")


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    task_id: Optional[str] = Field(None, description="ID of the task that caused the error")
