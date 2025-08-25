"""
Scheduler Service for Task Execution

This module provides the core scheduling functionality using APScheduler,
integrating with the Messaging Service for reliable task execution.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job as APSchedulerJob

from models.task_models import Task, TaskType, RepeatInterval
from services.messaging import MessagingService, Message
from utils.logger import get_logger


class SchedulerService:
    """
    Scheduler service for managing task scheduling and execution
    
    Integrates with APScheduler for scheduling and Messaging Service for execution.
    """
    
    def __init__(self, messaging_service: MessagingService):
        """
        Initialize the scheduler service
        
        Args:
            messaging_service: Service for sending messages to execute tasks
        """
        self.messaging_service = messaging_service
        self.logger = get_logger(__name__)
        
        # Configure scheduler with configurable backend
        jobstores = {
            'default': MemoryJobStore()  # Switch to RedisJobStore later
        }
        self.scheduler = AsyncIOScheduler(jobstores=jobstores)
        self._task_jobs: Dict[str, str] = {}  # task_id -> job_id mapping

    async def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()

    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            # Wait a bit for the scheduler to fully stop
            import asyncio
            await asyncio.sleep(0.1)

    async def schedule_task(self, task: Task) -> bool:
        """
        Schedule a task based on its type and timing
        
        Args:
            task: Task to schedule
            
        Returns:
            True if task was scheduled successfully, False otherwise
        """
        try:
            if task.task_type == TaskType.SCHEDULED:
                return await self._schedule_one_time_task(task)
            elif task.task_type == TaskType.REPEATED:
                return await self._schedule_recurring_task(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
        except Exception as e:
            self.logger.error(f"Failed to schedule task {task.id}: {e}")
            return False

    async def _schedule_one_time_task(self, task: Task) -> bool:
        """Schedule a one-time task"""
        try:
            job_id = f"task_{task.id}"
            self.scheduler.add_job(
                self._execute_task,
                'date',
                run_date=task.scheduled_at,
                args=[task.id],
                id=job_id,
                replace_existing=True
            )
            self._task_jobs[task.id] = job_id
            return True
        except Exception as e:
            self.logger.error(f"Failed to schedule one-time task {task.id}: {e}")
            return False

    async def _schedule_recurring_task(self, task: Task) -> bool:
        """Schedule a recurring task with standard intervals"""
        try:
            job_id = f"task_{task.id}"
            
            if task.repeat_interval == RepeatInterval.CUSTOM and task.cron_expression:
                # Handle custom cron expression
                self.scheduler.add_job(
                    self._execute_task,
                    CronTrigger.from_crontab(task.cron_expression),
                    args=[task.id],
                    id=job_id,
                    replace_existing=True
                )
            elif task.repeat_interval == RepeatInterval.DAILY:
                # Daily at specific time
                self.scheduler.add_job(
                    self._execute_task,
                    'cron',
                    hour=task.scheduled_at.hour,
                    minute=task.scheduled_at.minute,
                    args=[task.id],
                    id=job_id,
                    replace_existing=True
                )
            elif task.repeat_interval == RepeatInterval.WEEKLY:
                # Weekly on specific day and time
                self.scheduler.add_job(
                    self._execute_task,
                    'cron',
                    day_of_week=task.scheduled_at.weekday(),
                    hour=task.scheduled_at.hour,
                    minute=task.scheduled_at.minute,
                    args=[task.id],
                    id=job_id,
                    replace_existing=True
                )
            elif task.repeat_interval == RepeatInterval.MONTHLY:
                # Monthly on specific day and time
                self.scheduler.add_job(
                    self._execute_task,
                    'cron',
                    day=task.scheduled_at.day,
                    hour=task.scheduled_at.hour,
                    minute=task.scheduled_at.minute,
                    args=[task.id],
                    id=job_id,
                    replace_existing=True
                )
            else:
                raise ValueError(f"Invalid repeat interval: {task.repeat_interval}")
            
            self._task_jobs[task.id] = job_id
            return True
        except Exception as e:
            self.logger.error(f"Failed to schedule recurring task {task.id}: {e}")
            return False

    async def _execute_task(self, task_id: str):
        """
        Execute a scheduled task by creating a message in the Messaging Service
        
        Args:
            task_id: ID of the task to execute
        """
        try:
            message = Message(
                type="scheduled_task",
                payload={"task_id": task_id},
                correlation_id=f"task_{task_id}"
            )
            
            await self.messaging_service.send_message(message)
            self.logger.info(f"Task {task_id} execution message sent to messaging service")
        except Exception as e:
            self.logger.error(f"Failed to execute task {task_id}: {e}")

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was cancelled successfully, False otherwise
        """
        try:
            job_id = self._task_jobs.get(task_id)
            if job_id:
                self.scheduler.remove_job(job_id)
                del self._task_jobs[task_id]
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to cancel task {task_id}: {e}")
            return False

    async def pause_task(self, task_id: str) -> bool:
        """
        Pause a scheduled task
        
        Args:
            task_id: ID of the task to pause
            
        Returns:
            True if task was paused successfully, False otherwise
        """
        try:
            job_id = self._task_jobs.get(task_id)
            if job_id:
                self.scheduler.pause_job(job_id)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to pause task {task_id}: {e}")
            return False

    async def resume_task(self, task_id: str) -> bool:
        """
        Resume a paused task
        
        Args:
            task_id: ID of the task to resume
            
        Returns:
            True if task was resumed successfully, False otherwise
        """
        try:
            job_id = self._task_jobs.get(task_id)
            if job_id:
                self.scheduler.resume_job(job_id)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to resume task {task_id}: {e}")
            return False

    def get_scheduled_jobs(self) -> list[APSchedulerJob]:
        """Get all scheduled jobs"""
        return self.scheduler.get_jobs()

    def get_task_job(self, task_id: str) -> Optional[APSchedulerJob]:
        """Get the scheduled job for a specific task"""
        job_id = self._task_jobs.get(task_id)
        if job_id:
            return self.scheduler.get_job(job_id)
        return None

    def is_task_scheduled(self, task_id: str) -> bool:
        """Check if a task is currently scheduled"""
        return task_id in self._task_jobs

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status information"""
        return {
            "running": self.scheduler.running,
            "job_count": len(self.scheduler.get_jobs()),
            "task_jobs_count": len(self._task_jobs)
        }
