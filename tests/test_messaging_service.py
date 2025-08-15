"""
Tests for Messaging Service

Tests the core functionality of the messaging service including
job creation, status tracking, and queue operations.
"""

import pytest
import asyncio
from datetime import datetime
from services.messaging.models import Job, Message, JobStatus, JobPriority
from services.messaging.job_queue import InMemoryJobQueue
from services.messaging.messaging_service import MessagingService


@pytest.fixture
async def job_queue():
    """Create a test job queue"""
    queue = InMemoryJobQueue(backup_file="test_jobs_backup.json")
    yield queue
    # Cleanup
    import os
    if os.path.exists("test_jobs_backup.json"):
        os.remove("test_jobs_backup.json")


@pytest.fixture
async def messaging_service(job_queue):
    """Create a test messaging service"""
    service = MessagingService(job_queue)
    await service.start()
    yield service
    await service.stop()


@pytest.mark.asyncio
async def test_job_creation(messaging_service):
    """Test creating and submitting a job"""
    # Create a test job
    job = Job(
        type="test_job",
        payload={"test": "data"},
        priority=JobPriority.HIGH
    )
    
    # Submit the job
    job_id = await messaging_service.submit_job(job)
    
    # Verify job was created
    assert job_id is not None
    assert job_id == job.id
    
    # Check job status
    retrieved_job = await messaging_service.get_job_status(job_id)
    assert retrieved_job is not None
    assert retrieved_job.type == "test_job"
    assert retrieved_job.status == JobStatus.PENDING


@pytest.mark.asyncio
async def test_message_sending(messaging_service):
    """Test sending a message"""
    # Create a test message
    message = Message(
        type="test_message",
        payload={"message": "hello"},
        correlation_id="test_123"
    )
    
    # Send the message
    job_id = await messaging_service.send_message(message)
    
    # Verify message was processed
    assert job_id is not None
    
    # Check the resulting job
    job = await messaging_service.get_job_status(job_id)
    assert job is not None
    assert job.type == "test_message"
    assert job.payload == {"message": "hello"}
    assert job.metadata["correlation_id"] == "test_123"


@pytest.mark.asyncio
async def test_job_status_tracking(messaging_service):
    """Test job status updates"""
    # Create and submit a job
    job = Job(type="status_test", payload={})
    job_id = await messaging_service.submit_job(job)
    
    # Update job status
    success = await messaging_service.job_queue.update_job_status(
        job_id, JobStatus.RUNNING
    )
    assert success is True
    
    # Check updated status
    updated_job = await messaging_service.get_job_status(job_id)
    assert updated_job.status == JobStatus.RUNNING
    assert updated_job.started_at is not None


@pytest.mark.asyncio
async def test_queue_statistics(messaging_service):
    """Test queue statistics"""
    # Create some test jobs
    for i in range(3):
        job = Job(type=f"test_job_{i}", payload={"index": i})
        await messaging_service.submit_job(job)
    
    # Get queue stats
    stats = await messaging_service.get_queue_stats()
    
    # Verify stats
    assert stats["total_jobs"] >= 3
    assert stats["pending_jobs"] >= 3
    assert stats["service_status"] == "running"


@pytest.mark.asyncio
async def test_health_check(messaging_service):
    """Test health check functionality"""
    # Perform health check
    health = await messaging_service.health_check()
    
    # Verify health status
    assert health["status"] in ["healthy", "degraded"]
    assert health["service"] == "running"
    assert "queue" in health
    assert "handlers" in health


@pytest.mark.asyncio
async def test_job_cancellation(messaging_service):
    """Test job cancellation"""
    # Create and submit a job
    job = Job(type="cancellable", payload={})
    job_id = await messaging_service.submit_job(job)
    
    # Cancel the job
    success = await messaging_service.cancel_job(job_id)
    assert success is True
    
    # Check job status
    cancelled_job = await messaging_service.get_job_status(job_id)
    assert cancelled_job.status == JobStatus.CANCELLED


@pytest.mark.asyncio
async def test_jobs_by_status(messaging_service):
    """Test filtering jobs by status"""
    # Create jobs with different statuses
    job1 = Job(type="job1", payload={})
    job2 = Job(type="job2", payload={})
    
    await messaging_service.submit_job(job1)
    await messaging_service.submit_job(job2)
    
    # Update one job to completed
    await messaging_service.job_queue.update_job_status(
        job1.id, JobStatus.COMPLETED, result={"success": True}
    )
    
    # Get jobs by status
    pending_jobs = await messaging_service.get_jobs_by_status(JobStatus.PENDING)
    completed_jobs = await messaging_service.get_jobs_by_status(JobStatus.COMPLETED)
    
    # Verify filtering
    assert len(pending_jobs) >= 1
    assert len(completed_jobs) >= 1
    
    # Check that job1 is in completed
    job1_completed = next((j for j in completed_jobs if j.id == job1.id), None)
    assert job1_completed is not None
    assert job1_completed.result == {"success": True}


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
