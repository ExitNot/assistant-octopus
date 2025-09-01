"""
Tests for Scheduler Service

This module tests the core functionality of the scheduler service,
including task creation, scheduling, and execution.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from models.task_models import Task, TaskType, RepeatInterval
from services.scheduler import SchedulerService, TaskService
from services.messaging import MessagingService


@pytest.fixture
def mock_messaging_service():
    """Create a mock messaging service"""
    service = AsyncMock(spec=MessagingService)
    service.send_message = AsyncMock()
    return service


@pytest.fixture
def scheduler_service(mock_messaging_service):
    """Create a scheduler service with mock dependencies"""
    return SchedulerService(mock_messaging_service)


@pytest.fixture
def task_service(scheduler_service):
    """Create a task service with scheduler service"""
    return TaskService(scheduler_service)


@pytest.fixture
def sample_task():
    """Create a sample task for testing"""
    return Task(
        name="Test Task",
        description="A test task",
        task_type=TaskType.SCHEDULED,
        payload={"test": "data"},
        scheduled_at=datetime.now() + timedelta(minutes=5)
    )


@pytest.fixture
def sample_recurring_task():
    """Create a sample recurring task for testing"""
    return Task(
        name="Daily Task",
        description="A daily recurring task",
        task_type=TaskType.REPEATED,
        payload={"test": "data"},
        scheduled_at=datetime.now() + timedelta(minutes=5),
        repeat_interval=RepeatInterval.DAILY
    )


class TestSchedulerService:
    """Test cases for SchedulerService"""
    
    @pytest.mark.asyncio
    async def test_scheduler_initialization(self, scheduler_service):
        """Test scheduler service initialization"""
        assert scheduler_service.scheduler is not None
        assert not scheduler_service.scheduler.running
    
    @pytest.mark.asyncio
    async def test_start_stop_scheduler(self, scheduler_service):
        """Test starting and stopping the scheduler"""
        await scheduler_service.start()
        assert scheduler_service.scheduler.running
        
        await scheduler_service.stop()
        assert not scheduler_service.scheduler.running
    
    @pytest.mark.asyncio
    async def test_schedule_one_time_task(self, scheduler_service, sample_task):
        """Test scheduling a one-time task"""
        await scheduler_service.start()
        
        result = await scheduler_service.schedule_task(sample_task)
        assert result is True
        
        # Check if job was created
        assert scheduler_service.is_task_scheduled(sample_task.id)
        
        await scheduler_service.stop()
    
    @pytest.mark.asyncio
    async def test_schedule_recurring_task(self, scheduler_service, sample_recurring_task):
        """Test scheduling a recurring task"""
        await scheduler_service.start()
        
        result = await scheduler_service.schedule_task(sample_recurring_task)
        assert result is True
        
        # Check if job was created
        assert scheduler_service.is_task_scheduled(sample_recurring_task.id)
        
        await scheduler_service.stop()
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, scheduler_service, sample_task):
        """Test cancelling a scheduled task"""
        await scheduler_service.start()
        await scheduler_service.schedule_task(sample_task)
        
        result = await scheduler_service.cancel_task(sample_task.id)
        assert result is True
        
        # Check if job was removed
        assert not scheduler_service.is_task_scheduled(sample_task.id)
        
        await scheduler_service.stop()


class TestTaskService:
    """Test cases for TaskService"""
    
    @pytest.mark.asyncio
    async def test_create_task(self, task_service, sample_task):
        """Test creating a new task"""
        created_task = await task_service.create_task(sample_task)
        
        assert created_task.id is not None
        assert created_task.name == sample_task.name
        assert created_task.created_at is not None
        assert created_task.updated_at is not None
        
        # Check if task is stored
        stored_task = await task_service.get_task(created_task.id)
        assert stored_task is not None
        assert stored_task.id == created_task.id
    
    @pytest.mark.asyncio
    async def test_get_tasks(self, task_service, sample_task):
        """Test retrieving tasks with filtering"""
        # Create multiple tasks
        await task_service.create_task(sample_task)
        
        # Create another task
        task2 = Task(
            name="Task 2",
            task_type=TaskType.REPEATED,
            payload={},
            scheduled_at=datetime.now() + timedelta(minutes=10),
            repeat_interval=RepeatInterval.DAILY
        )
        await task_service.create_task(task2)
        
        # Get all tasks
        all_tasks = await task_service.get_tasks()
        assert len(all_tasks) == 2
        
        # Filter by task type
        scheduled_tasks = await task_service.get_tasks(task_type=TaskType.SCHEDULED)
        assert len(scheduled_tasks) == 1
        assert scheduled_tasks[0].task_type == TaskType.SCHEDULED
        
        # Filter by active status
        active_tasks = await task_service.get_tasks(is_active=True)
        assert len(active_tasks) == 2
    
    @pytest.mark.asyncio
    async def test_update_task(self, task_service, sample_task):
        """Test updating a task"""
        created_task = await task_service.create_task(sample_task)
        
        # Capture the timestamp before update
        original_updated_at = created_task.updated_at
        
        # Add a small delay to ensure timestamps are different
        import asyncio
        await asyncio.sleep(0.01)
        
        # Update task
        updates = {"name": "Updated Task Name"}
        updated_task = await task_service.update_task(created_task.id, updates)
        
        assert updated_task.name == "Updated Task Name"
        assert updated_task.updated_at > original_updated_at
    
    @pytest.mark.asyncio
    async def test_delete_task(self, task_service, sample_task):
        """Test deleting a task"""
        created_task = await task_service.create_task(sample_task)
        
        # Delete task
        result = await task_service.delete_task(created_task.id)
        assert result is True
        
        # Check if task is removed
        stored_task = await task_service.get_task(created_task.id)
        assert stored_task is None
    
    @pytest.mark.asyncio
    async def test_task_validation(self, task_service):
        """Test task validation"""
        # Test missing name
        invalid_task = Task(
            name="",  # Empty name
            task_type=TaskType.SCHEDULED,
            payload={},
            scheduled_at=datetime.now() + timedelta(minutes=5)
        )
        
        with pytest.raises(ValueError, match="Task name is required"):
            await task_service.create_task(invalid_task)
        
        # Test past scheduled time for one-time task
        past_task = Task(
            name="Past Task",
            task_type=TaskType.SCHEDULED,
            payload={},
            scheduled_at=datetime.now() - timedelta(minutes=5)  # Past time
        )
        
        with pytest.raises(ValueError, match="Scheduled time must be in the future"):
            await task_service.create_task(past_task)
    
    @pytest.mark.asyncio
    async def test_task_control_operations(self, task_service, sample_task):
        """Test task control operations (pause, resume, cancel)"""
        created_task = await task_service.create_task(sample_task)
        
        # Pause task
        result = await task_service.pause_task(created_task.id)
        assert result is True
        
        # Check if task is inactive
        paused_task = await task_service.get_task(created_task.id)
        assert paused_task.is_active is False
        
        # Resume task
        result = await task_service.resume_task(created_task.id)
        assert result is True
        
        # Check if task is active again
        resumed_task = await task_service.get_task(created_task.id)
        assert resumed_task.is_active is True
        
        # Cancel task
        result = await task_service.cancel_task(created_task.id)
        assert result is True
        
        # Check if task is inactive
        cancelled_task = await task_service.get_task(created_task.id)
        assert cancelled_task.is_active is False


if __name__ == "__main__":
    pytest.main([__file__])
