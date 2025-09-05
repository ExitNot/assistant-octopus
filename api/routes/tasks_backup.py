"""
Task Management API Routes

This module provides the REST API endpoints for task management,
including CRUD operations and task control functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends

from api.models.task_models import (
    CreateTaskRequest,
    UpdateTaskRequest,
    TaskResponse,
    TaskListResponse,
    TaskControlResponse
)
from models.task_models import Task, TaskType
from services.scheduler import TaskService, SchedulerService
from services.messaging import MessagingService
from services.service_registry import service_registry

# Create tasks_router
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


# Dependency injection
async def get_task_service() -> TaskService:
    """Get task service instance from registry"""
    task_service = service_registry.get_task_service()
    if task_service is None:
        raise HTTPException(
            status_code=503, 
            detail="Task service not initialized. Please start the CLI server first."
        )
    return task_service


async def get_scheduler_service() -> SchedulerService:
    """Get scheduler service instance from registry"""
    scheduler_service = service_registry.get_scheduler_service()
    if scheduler_service is None:
        raise HTTPException(
            status_code=503, 
            detail="Scheduler service not initialized. Please start the CLI server first."
        )
    return scheduler_service


async def get_messaging_service() -> MessagingService:
    """Get messaging service instance from registry"""
    messaging_service = service_registry.get_messaging_service()
    if messaging_service is None:
        raise HTTPException(
            status_code=503, 
            detail="Messaging service not initialized. Please start the CLI server first."
        )
    return messaging_service

@tasks_router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    request: CreateTaskRequest,
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Create a new scheduled or repeated task
    
    Args:
        request: Task creation data
        task_service: Task service instance
        
    Returns:
        Created task
        
    Raises:
        HTTPException: If task creation fails
    """
    try:
        task = Task(
            name=request.name,
            description=request.description,
            task_type=request.task_type,
            payload=request.payload,
            scheduled_at=request.scheduled_at,
            repeat_interval=request.repeat_interval,
            cron_expression=request.cron_expression
        )
        
        created_task = await task_service.create_task(task)
        
        return TaskResponse(
            id=created_task.id,
            name=created_task.name,
            description=created_task.description,
            task_type=created_task.task_type,
            payload=created_task.payload,
            scheduled_at=created_task.scheduled_at,
            repeat_interval=created_task.repeat_interval,
            cron_expression=created_task.cron_expression,
            is_active=created_task.is_active,
            created_at=created_task.created_at,
            updated_at=created_task.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@tasks_router.get("/", response_model=TaskListResponse)
async def get_tasks(
    task_type: Optional[TaskType] = Query(None, description="Filter by task type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(100, ge=1, le=1000, description="Page size"),
    task_service: TaskService = Depends(get_task_service)
) -> TaskListResponse:
    """
    Get list of tasks with optional filtering and pagination
    
    Args:
        task_type: Filter by task type
        is_active: Filter by active status
        page: Page number (1-based)
        size: Page size
        task_service: Task service instance
        
    Returns:
        Paginated list of tasks
    """
    try:
        offset = (page - 1) * size
        tasks = await task_service.get_tasks(
            task_type=task_type,
            is_active=is_active,
            limit=size,
            offset=offset
        )
        total = await task_service.get_task_count(task_type=task_type, is_active=is_active)
        
        task_responses = [
            TaskResponse(
                id=task.id,
                name=task.name,
                description=task.description,
                task_type=task.task_type,
                payload=task.payload,
                scheduled_at=task.scheduled_at,
                repeat_interval=task.repeat_interval,
                cron_expression=task.cron_expression,
                is_active=task.is_active,
                created_at=task.created_at,
                updated_at=task.updated_at
            )
            for task in tasks
        ]
        
        return TaskListResponse(
            tasks=task_responses,
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")


@tasks_router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Get a specific task by ID
    
    Args:
        task_id: Task identifier
        task_service: Task service instance
        
    Returns:
        Task details
        
    Raises:
        HTTPException: If task not found
    """
    try:
        task = await task_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            task_type=task.task_type,
            payload=task.payload,
            scheduled_at=task.scheduled_at,
            repeat_interval=task.repeat_interval,
            cron_expression=task.cron_expression,
            is_active=task.is_active,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@tasks_router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    servicies: Servicies = Depends(get_servicies)
) -> TaskResponse:
    """
    Update an existing task
    
    Args:
        task_id: Task identifier
        request: Task update data
        task_service: Task service instance
        
    Returns:
        Updated task
        
    Raises:
        HTTPException: If task not found or update fails
    """
    try:
        # Convert request to updates dictionary
        updates = {}
        if request.name is not None:
            updates['name'] = request.name
        if request.description is not None:
            updates['description'] = request.description
        if request.payload is not None:
            updates['payload'] = request.payload
        if request.scheduled_at is not None:
            updates['scheduled_at'] = request.scheduled_at
        if request.repeat_interval is not None:
            updates['repeat_interval'] = request.repeat_interval
        if request.cron_expression is not None:
            updates['cron_expression'] = request.cron_expression
        if request.is_active is not None:
            updates['is_active'] = request.is_active
        
        # Update task
        updated_task = await servicies.task_service.update_task(task_id, updates)
        if not updated_task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            id=updated_task.id,
            name=updated_task.name,
            description=updated_task.description,
            task_type=updated_task.task_type,
            payload=updated_task.payload,
            scheduled_at=updated_task.scheduled_at,
            repeat_interval=updated_task.repeat_interval,
            cron_expression=updated_task.cron_expression,
            is_active=updated_task.is_active,
            created_at=updated_task.created_at,
            updated_at=updated_task.updated_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")


@tasks_router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    servicies: Servicies = Depends(get_servicies)
):
    """
    Delete a task and cancel all related jobs
    
    Args:
        task_id: Task identifier
        task_service: Task service instance
        
    Raises:
        HTTPException: If task not found or deletion fails
    """
    try:
        success = await servicies.task_service.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


@tasks_router.post("/{task_id}/pause", response_model=TaskControlResponse)
async def pause_task(
    task_id: str,
    servicies: Servicies = Depends(get_servicies)
) -> TaskControlResponse:
    """
    Pause a task
    
    Args:
        task_id: Task identifier
        task_service: Task service instance
        
    Returns:
        Operation result
        
    Raises:
        HTTPException: If task not found or operation fails
    """
    try:
        success = await servicies.task_service.pause_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskControlResponse(
            success=True,
            message="Task paused successfully",
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause task: {str(e)}")


@tasks_router.post("/{task_id}/resume", response_model=TaskControlResponse)
async def resume_task(
    task_id: str,
    servicies: Servicies = Depends(get_servicies)
) -> TaskControlResponse:
    """
    Resume a paused task
    
    Args:
        task_id: Task identifier
        task_service: Task service instance
        
    Returns:
        Operation result
        
    Raises:
        HTTPException: If task not found or operation fails
    """
    try:
        success = await servicies.task_service.resume_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskControlResponse(
            success=True,
            message="Task resumed successfully",
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume task: {str(e)}")


@tasks_router.post("/{task_id}/cancel", response_model=TaskControlResponse)
async def cancel_task(
    task_id: str,
    servicies: Servicies = Depends(get_servicies)
) -> TaskControlResponse:
    """
    Cancel a task (remove from scheduler but keep in storage)
    
    Args:
        task_id: Task identifier
        task_service: Task service instance
        
    Returns:
        Operation result
        
    Raises:
        HTTPException: If task not found or operation fails
    """
    try:
        success = await servicies.task_service.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskControlResponse(
            success=True,
            message="Task cancelled successfully",
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@tasks_router.get("/{task_id}/status")
async def get_task_status(
    task_id: str,
    servicies: Servicies = Depends(get_servicies)
):
    """
    Get task status and scheduling information
    
    Args:
        task_id: Task identifier
        task_service: Task service instance
        
    Returns:
        Task status information
        
    Raises:
        HTTPException: If task not found
    """
    try:
        task = await servicies.task_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get scheduler status for this task
        is_scheduled = servicies.scheduler_service.is_task_scheduled(task_id)
        job = servicies.scheduler_service.get_task_job(task_id)
        
        status_info = {
            "task_id": task_id,
            "is_active": task.is_active,
            "is_scheduled": is_scheduled,
            "next_run": None,
            "job_status": None
        }
        
        if job:
            status_info["next_run"] = job.next_run_time.isoformat() if job.next_run_time else None
            status_info["job_status"] = "paused" if job.paused else "active"
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")
