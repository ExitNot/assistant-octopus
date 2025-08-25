"""
Messaging Service Router

Provides REST API endpoints for the messaging service, including
job submission, status checking, and health monitoring.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from pydantic import BaseModel

from ...models.messaging_models import Job, Message, JobStatus, JobPriority
from .factory import get_messaging_service

# Pydantic models for API requests/responses
class CreateJobRequest(BaseModel):
    type: str
    payload: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    scheduled_at: str = None  # ISO format datetime string
    max_retries: int = 3
    metadata: Dict[str, Any] = None

class CreateMessageRequest(BaseModel):
    type: str
    payload: Dict[str, Any]
    correlation_id: str = None

class JobResponse(BaseModel):
    id: str
    type: str
    status: str
    priority: int
    created_at: str
    started_at: str = None
    completed_at: str = None
    result: Dict[str, Any] = None
    error: str = None
    retry_count: int
    max_retries: int

class QueueStatsResponse(BaseModel):
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    service_status: str
    registered_handlers: int
    message_types: List[str]

class HealthCheckResponse(BaseModel):
    status: str
    service: str
    queue: Dict[str, Any]
    handlers: Dict[str, Any]
    timestamp: str

# Create router
messaging_router = APIRouter(prefix="/messaging", tags=["Messaging"])

@messaging_router.post("/jobs", response_model=Dict[str, str])
async def create_job(request: CreateJobRequest):
    """
    Create and submit a new job
    
    Args:
        request: Job creation parameters
        
    Returns:
        Job ID for tracking
    """
    try:
        messaging_service = get_messaging_service()
        
        # Create job from request
        job = Job(
            type=request.type,
            payload=request.payload,
            priority=request.priority,
            max_retries=request.max_retries,
            metadata=request.metadata
        )
        
        # Submit job
        job_id = await messaging_service.submit_job(job)
        
        return {"job_id": job_id, "status": "submitted"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )

@messaging_router.post("/messages", response_model=Dict[str, str])
async def send_message(request: CreateMessageRequest):
    """
    Send a message for processing
    
    Args:
        request: Message parameters
        
    Returns:
        Job ID for tracking the message processing
    """
    try:
        messaging_service = get_messaging_service()
        
        # Create message from request
        message = Message(
            type=request.type,
            payload=request.payload,
            correlation_id=request.correlation_id
        )
        
        # Send message
        job_id = await messaging_service.send_message(message)
        
        return {"job_id": job_id, "status": "sent"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@messaging_router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a specific job
    
    Args:
        job_id: ID of the job to check
        
    Returns:
        Job status and details
    """
    try:
        messaging_service = get_messaging_service()
        job = await messaging_service.get_job_status(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Convert to response model
        return JobResponse(
            id=job.id,
            type=job.type,
            status=job.status.value,
            priority=job.priority.value,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            result=job.result,
            error=job.error,
            retry_count=job.retry_count,
            max_retries=job.max_retries
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )

@messaging_router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a pending job
    
    Args:
        job_id: ID of the job to cancel
        
    Returns:
        Success status
    """
    try:
        messaging_service = get_messaging_service()
        success = await messaging_service.cancel_job(job_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job cannot be cancelled or not found"
            )
        
        return {"status": "cancelled", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )

@messaging_router.get("/jobs", response_model=List[JobResponse])
async def list_jobs_by_status(status: JobStatus = None):
    """
    List jobs by status
    
    Args:
        status: Optional status filter
        
    Returns:
        List of jobs matching the criteria
    """
    try:
        messaging_service = get_messaging_service()
        
        if status:
            jobs = await messaging_service.get_jobs_by_status(status)
        else:
            # Get all jobs by getting from each status
            all_jobs = []
            for job_status in JobStatus:
                jobs = await messaging_service.get_jobs_by_status(job_status)
                all_jobs.extend(jobs)
            jobs = all_jobs
        
        # Convert to response models
        return [
            JobResponse(
                id=job.id,
                type=job.type,
                status=job.status.value,
                priority=job.priority.value,
                created_at=job.created_at.isoformat(),
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                result=job.result,
                error=job.error,
                retry_count=job.retry_count,
                max_retries=job.max_retries
            )
            for job in jobs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )

@messaging_router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_stats():
    """
    Get comprehensive queue statistics
    
    Returns:
        Queue metrics and service information
    """
    try:
        messaging_service = get_messaging_service()
        stats = await messaging_service.get_queue_stats()
        return QueueStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue stats: {str(e)}"
        )

@messaging_router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Perform a comprehensive health check
    
    Returns:
        Service health status
    """
    try:
        messaging_service = get_messaging_service()
        health = await messaging_service.health_check()
        return HealthCheckResponse(**health)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform health check: {str(e)}"
        )
