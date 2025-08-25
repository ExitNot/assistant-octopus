"""
Job Queue Implementation for Messaging Service

This module provides the JobQueue interface and InMemoryJobQueue implementation
with priority queuing, persistence, and recovery capabilities.
"""

import asyncio
import json
import aiofiles
from typing import Dict, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from models.messaging_models import Job, JobStatus, JobPriority


class JobQueue(ABC):
    """Abstract interface for job queue implementations"""
    
    @abstractmethod
    async def enqueue(self, job: Job) -> None:
        """Add a job to the queue"""
        pass
    
    @abstractmethod
    async def dequeue(self, priority: bool = True) -> Optional[Job]:
        """Remove and return the next job from the queue"""
        pass
    
    @abstractmethod
    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get the current status of a specific job"""
        pass
    
    @abstractmethod
    async def update_job_status(self, job_id: str, status: JobStatus, **kwargs) -> bool:
        """Update the status of a specific job"""
        pass
    
    @abstractmethod
    async def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """Get all jobs with a specific status"""
        pass
    
    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job"""
        pass
    
    @abstractmethod
    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        pass


class InMemoryJobQueue(JobQueue):
    """
    In-memory job queue implementation with priority queuing and persistence
    
    Features:
    - Priority-based job processing (URGENT > HIGH > NORMAL > LOW)
    - File-based persistence for container restart recovery
    - Job status tracking and management
    - Configurable retry mechanisms
    """
    
    def __init__(self, backup_file: str = "jobs_backup.json"):
        self._queues = {
            JobPriority.URGENT: asyncio.Queue(),
            JobPriority.HIGH: asyncio.Queue(),
            JobPriority.NORMAL: asyncio.Queue(),
            JobPriority.LOW: asyncio.Queue()
        }
        self._jobs: Dict[str, Job] = {}
        self._backup_file = backup_file
        self._lock = asyncio.Lock()
        self._stats = {
            "total_jobs": 0,
            "pending_jobs": 0,
            "running_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "cancelled_jobs": 0
        }
    
    async def enqueue(self, job: Job) -> None:
        """Add a job to the appropriate priority queue"""
        async with self._lock:
            # Store job in memory
            self._jobs[job.id] = job
            
            # Add to appropriate priority queue
            await self._queues[job.priority].put(job)
            
            # Update statistics
            self._stats["total_jobs"] += 1
            self._stats["pending_jobs"] += 1
            
            # Persist to disk
            await self._backup_to_disk()
    
    async def dequeue(self, priority: bool = True) -> Optional[Job]:
        """Get the next job from the queue based on priority"""
        if priority:
            # Process higher priority queues first
            for priority_level in [JobPriority.URGENT, JobPriority.HIGH, 
                                 JobPriority.NORMAL, JobPriority.LOW]:
                if not self._queues[priority_level].empty():
                    job = await self._queues[priority_level].get()
                    
                    # Update job status to running (this will update stats automatically)
                    await self.update_job_status(job.id, JobStatus.RUNNING)
                    
                    return job
        else:
            # Round-robin across all queues
            for _ in range(sum(q.qsize() for q in self._queues.values())):
                for priority_level in [JobPriority.URGENT, JobPriority.HIGH, 
                                     JobPriority.NORMAL, JobPriority.LOW]:
                    if not self._queues[priority_level].empty():
                        job = await self._queues[priority_level].get()
                        
                        # Update job status to running (this will update stats automatically)
                        await self.update_job_status(job.id, JobStatus.RUNNING)
                        
                        return job
        
        return None
    
    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get the current status of a specific job"""
        return self._jobs.get(job_id)
    
    async def update_job_status(self, job_id: str, status: JobStatus, **kwargs) -> bool:
        """Update the status of a specific job with additional fields"""
        if job_id not in self._jobs:
            return False
        
        job = self._jobs[job_id]
        old_status = job.status
        job.status = status
        
        # Update additional fields
        if status == JobStatus.RUNNING and 'started_at' not in kwargs:
            job.started_at = datetime.now()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED] and 'completed_at' not in kwargs:
            job.completed_at = datetime.now()
        
        # Update any other provided fields
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        # Update statistics
        self._update_stats(old_status, status)
        
        # Persist changes to disk
        await self._backup_to_disk()
        return True
    
    async def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """Get all jobs with a specific status"""
        return [job for job in self._jobs.values() if job.status == status]
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job"""
        if job_id not in self._jobs:
            return False
        
        job = self._jobs[job_id]
        if job.status == JobStatus.PENDING:
            # Mark as cancelled
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            
            # Update statistics
            self._stats["pending_jobs"] -= 1
            self._stats["cancelled_jobs"] += 1
            
            # Persist changes
            await self._backup_to_disk()
            return True
        
        return False
    
    async def get_queue_stats(self) -> Dict[str, int]:
        """Get current queue statistics"""
        # Calculate current queue sizes
        queue_sizes = {
            f"queue_{priority.name.lower()}": q.qsize()
            for priority, q in self._queues.items()
        }
        
        return {**self._stats, **queue_sizes}
    
    async def cleanup_completed_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up old completed jobs to free memory"""
        cutoff_time = datetime.now().replace(
            hour=datetime.now().hour - max_age_hours
        )
        
        jobs_to_remove = []
        for job_id, job in self._jobs.items():
            if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and
                job.completed_at and job.completed_at < cutoff_time):
                jobs_to_remove.append(job_id)
        
        # Remove old jobs and update statistics
        for job_id in jobs_to_remove:
            job = self._jobs[job_id]
            # Update stats before removing
            if job.status == JobStatus.COMPLETED:
                self._stats["completed_jobs"] = max(0, self._stats["completed_jobs"] - 1)
            elif job.status == JobStatus.FAILED:
                self._stats["failed_jobs"] = max(0, self._stats["failed_jobs"] - 1)
            elif job.status == JobStatus.CANCELLED:
                self._stats["cancelled_jobs"] = max(0, self._stats["cancelled_jobs"] - 1)
            
            del self._jobs[job_id]
        
        # Update total jobs count
        self._stats["total_jobs"] -= len(jobs_to_remove)
        
        # Persist changes
        await self._backup_to_disk()
        
        return len(jobs_to_remove)
    
    async def _backup_to_disk(self):
        """Persist jobs to disk for container restart recovery"""
        try:
            backup_data = {
                "jobs": {k: job.to_dict() for k, job in self._jobs.items()},
                "timestamp": datetime.now().isoformat(),
                "stats": self._stats
            }
            async with aiofiles.open(self._backup_file, 'w') as f:
                await f.write(json.dumps(backup_data, default=str, indent=2))
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Failed to backup jobs: {e}")
    
    async def restore_from_disk(self):
        """Restore jobs from disk after container restart"""
        try:
            async with aiofiles.open(self._backup_file, 'r') as f:
                content = await f.read()
                if content:
                    backup_data = json.loads(content)
                    
                    # Restore jobs
                    for job_id, job_data in backup_data.get("jobs", {}).items():
                        try:
                            job = Job.from_dict(job_data)
                            self._jobs[job_id] = job
                            
                            # Re-queue pending jobs
                            if job.status == JobStatus.PENDING:
                                await self._queues[job.priority].put(job)
                        except Exception as e:
                            print(f"Failed to restore job {job_id}: {e}")
                            continue
                    
                    # Restore statistics
                    if "stats" in backup_data:
                        self._stats.update(backup_data["stats"])
                    
                    print(f"Restored {len(self._jobs)} jobs from backup")
                    
        except FileNotFoundError:
            # No backup file exists yet
            print("No backup file found, starting with empty queue")
        except Exception as e:
            print(f"Failed to restore jobs: {e}")
    
    def _update_stats(self, old_status: JobStatus, new_status: JobStatus):
        """Update statistics when job status changes"""
        # Decrement old status count
        if old_status == JobStatus.PENDING:
            self._stats["pending_jobs"] = max(0, self._stats["pending_jobs"] - 1)
        elif old_status == JobStatus.RUNNING:
            self._stats["running_jobs"] = max(0, self._stats["running_jobs"] - 1)
        elif old_status == JobStatus.COMPLETED:
            self._stats["completed_jobs"] = max(0, self._stats["completed_jobs"] - 1)
        elif old_status == JobStatus.FAILED:
            self._stats["failed_jobs"] = max(0, self._stats["failed_jobs"] - 1)
        elif old_status == JobStatus.CANCELLED:
            self._stats["cancelled_jobs"] = max(0, self._stats["cancelled_jobs"] - 1)
        
        # Increment new status count
        if new_status == JobStatus.PENDING:
            self._stats["pending_jobs"] += 1
        elif new_status == JobStatus.RUNNING:
            self._stats["running_jobs"] += 1
        elif new_status == JobStatus.COMPLETED:
            self._stats["completed_jobs"] += 1
        elif new_status == JobStatus.FAILED:
            self._stats["failed_jobs"] += 1
        elif new_status == JobStatus.CANCELLED:
            self._stats["cancelled_jobs"] += 1
