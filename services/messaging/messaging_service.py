"""
Messaging Service Facade

This module provides a clean interface for other services to interact with
the messaging system, including job submission, status checking, and
message handling.
"""

from typing import Callable, Dict, Any, Optional, List
from ...models.messaging_models import Job, Message, JobStatus
from .job_queue import JobQueue
from datetime import datetime


class MessagingService:
    """
    Main messaging service facade that coordinates job queue operations
    
    Provides a simplified interface for other services to:
    - Submit jobs for processing
    - Check job status and results
    - Register message handlers
    - Monitor system health
    """
    
    def __init__(self, job_queue: JobQueue):
        self.job_queue = job_queue
        self.message_handlers: Dict[str, Callable] = {}
        self.is_running = False
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """
        Register a handler function for a specific message type
        
        Args:
            message_type: Type identifier for the message
            handler: Function to process messages of this type
        """
        self.message_handlers[message_type] = handler
    
    async def send_message(self, message: Message) -> str:
        """
        Send a message and return the job ID
        
        Args:
            message: Message to be processed
            
        Returns:
            Job ID for tracking the message processing
        """
        # Convert message to job
        job = Job(
            type=message.type,
            payload=message.payload,
            metadata={"correlation_id": message.correlation_id}
        )
        
        await self.job_queue.enqueue(job)
        return job.id
    
    async def submit_job(self, job: Job) -> str:
        """
        Submit a job directly to the queue
        
        Args:
            job: Job to be processed
            
        Returns:
            Job ID for tracking
        """
        await self.job_queue.enqueue(job)
        return job.id
    
    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """
        Get the status of a specific job
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Job object with current status, or None if not found
        """
        return await self.job_queue.get_job_status(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending job
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            True if job was cancelled, False otherwise
        """
        return await self.job_queue.cancel_job(job_id)
    
    async def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """
        Get all jobs with a specific status
        
        Args:
            status: Status to filter by
            
        Returns:
            List of jobs with the specified status
        """
        return await self.job_queue.get_jobs_by_status(status)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive queue statistics
        
        Returns:
            Dictionary containing queue metrics and health information
        """
        stats = await self.job_queue.get_queue_stats()
        
        # Add service health information
        stats.update({
            "service_status": "running" if self.is_running else "stopped",
            "registered_handlers": len(self.message_handlers),
            "message_types": list(self.message_handlers.keys())
        })
        
        return stats
    
    async def start(self):
        """Start the messaging service"""
        if self.is_running:
            return
        
        self.is_running = True
        # Restore any jobs from disk backup
        if hasattr(self.job_queue, 'restore_from_disk'):
            await self.job_queue.restore_from_disk()
    
    async def stop(self):
        """Stop the messaging service gracefully"""
        if not self.is_running:
            return
        
        self.is_running = False
        # Ensure all jobs are backed up to disk
        if hasattr(self.job_queue, '_backup_to_disk'):
            await self.job_queue._backup_to_disk()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check
        
        Returns:
            Health status information
        """
        try:
            # Check if service is running
            if not self.is_running:
                return {
                    "status": "unhealthy",
                    "error": "Service is not running",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Check queue health
            queue_stats = await self.job_queue.get_queue_stats()
            
            # Determine overall health based on queue status
            overall_status = "healthy"
            if queue_stats.get("failed_jobs", 0) > 10:  # Threshold for failed jobs
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "service": "running",
                "queue": queue_stats,
                "handlers": {
                    "count": len(self.message_handlers),
                    "types": list(self.message_handlers.keys())
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
