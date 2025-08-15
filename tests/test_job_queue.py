"""
Tests for JobQueue and InMemoryJobQueue implementation
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime

from services.messaging.job_queue import InMemoryJobQueue
from services.messaging.models import Job, JobStatus, JobPriority, Message


@pytest.fixture
def temp_backup_file():
    """Create a temporary backup file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write('{}')
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def job_queue(temp_backup_file):
    """Create a job queue instance for testing"""
    return InMemoryJobQueue(backup_file=temp_backup_file)


@pytest.fixture
def sample_jobs():
    """Create sample jobs for testing"""
    return [
        Job(
            id="job-1",
            type="test_task",
            payload={"data": "test1"},
            priority=JobPriority.LOW
        ),
        Job(
            id="job-2", 
            type="test_task",
            payload={"data": "test2"},
            priority=JobPriority.HIGH
        ),
        Job(
            id="job-3",
            type="test_task", 
            payload={"data": "test3"},
            priority=JobPriority.URGENT
        )
    ]


class TestInMemoryJobQueue:
    """Test cases for InMemoryJobQueue"""
    
    @pytest.mark.asyncio
    async def test_enqueue_and_dequeue_priority(self, job_queue, sample_jobs):
        """Test that jobs are dequeued in priority order"""
        # Enqueue jobs
        for job in sample_jobs:
            await job_queue.enqueue(job)
        
        # Dequeue with priority - should get URGENT first
        job1 = await job_queue.dequeue(priority=True)
        assert job1.id == "job-3"  # URGENT priority
        assert job1.priority == JobPriority.URGENT
        
        # Next should be HIGH priority
        job2 = await job_queue.dequeue(priority=True)
        assert job2.id == "job-2"  # HIGH priority
        assert job2.priority == JobPriority.HIGH
        
        # Finally LOW priority
        job3 = await job_queue.dequeue(priority=True)
        assert job3.id == "job-1"  # LOW priority
        assert job3.priority == JobPriority.LOW
    
    @pytest.mark.asyncio
    async def test_enqueue_and_dequeue_round_robin(self, job_queue, sample_jobs):
        """Test round-robin dequeueing when priority=False"""
        # Enqueue jobs
        for job in sample_jobs:
            await job_queue.enqueue(job)
        
        # Dequeue without priority - should get jobs in round-robin order
        jobs = []
        for _ in range(3):
            job = await job_queue.dequeue(priority=False)
            if job:
                jobs.append(job)
        
        # Should have dequeued all jobs
        assert len(jobs) == 3
        assert {job.id for job in jobs} == {"job-1", "job-2", "job-3"}
    
    @pytest.mark.asyncio
    async def test_job_status_tracking(self, job_queue):
        """Test job status tracking and updates"""
        # Create and enqueue a job
        job = Job(
            id="test-job",
            type="test_task",
            payload={"data": "test"}
        )
        await job_queue.enqueue(job)
        
        # Check initial status
        assert job.status == JobStatus.PENDING
        
        # Dequeue and check status update
        dequeued_job = await job_queue.dequeue()
        assert dequeued_job.status == JobStatus.RUNNING
        assert dequeued_job.started_at is not None
        
        # Update status to completed
        await job_queue.update_job_status(
            job.id, 
            JobStatus.COMPLETED, 
            result={"output": "success"}
        )
        
        # Verify status and result
        updated_job = await job_queue.get_job_status(job.id)
        assert updated_job.status == JobStatus.COMPLETED
        assert updated_job.result == {"output": "success"}
        assert updated_job.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_job_cancellation(self, job_queue):
        """Test job cancellation functionality"""
        # Create and enqueue a job
        job = Job(
            id="cancel-job",
            type="test_task",
            payload={"data": "test"}
        )
        await job_queue.enqueue(job)
        
        # Cancel the job
        success = await job_queue.cancel_job(job.id)
        assert success is True
        
        # Check job status
        cancelled_job = await job_queue.get_job_status(job.id)
        assert cancelled_job.status == JobStatus.CANCELLED
        assert cancelled_job.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_get_jobs_by_status(self, job_queue, sample_jobs):
        """Test retrieving jobs by status"""
        # Enqueue jobs
        for job in sample_jobs:
            await job_queue.enqueue(job)
        
        # Get pending jobs
        pending_jobs = await job_queue.get_jobs_by_status(JobStatus.PENDING)
        assert len(pending_jobs) == 3
        
        # Dequeue one job to change its status
        await job_queue.dequeue()
        
        # Check counts
        pending_jobs = await job_queue.get_jobs_by_status(JobStatus.PENDING)
        running_jobs = await job_queue.get_jobs_by_status(JobStatus.RUNNING)
        
        assert len(pending_jobs) == 2
        assert len(running_jobs) == 1
    
    @pytest.mark.asyncio
    async def test_queue_statistics(self, job_queue, sample_jobs):
        """Test queue statistics tracking"""
        # Check initial stats
        stats = await job_queue.get_queue_stats()
        assert stats["total_jobs"] == 0
        assert stats["pending_jobs"] == 0
        
        # Enqueue jobs
        for job in sample_jobs:
            await job_queue.enqueue(job)
        
        # Check stats after enqueueing
        stats = await job_queue.get_queue_stats()
        assert stats["total_jobs"] == 3
        assert stats["pending_jobs"] == 3
        assert stats["queue_urgent"] == 1
        assert stats["queue_high"] == 1
        assert stats["queue_normal"] == 0
        assert stats["queue_low"] == 1
        
        # Dequeue a job and check stats
        await job_queue.dequeue()
        stats = await job_queue.get_queue_stats()
        assert stats["pending_jobs"] == 2
        assert stats["running_jobs"] == 1
    
    @pytest.mark.asyncio
    async def test_persistence_and_recovery(self, temp_backup_file):
        """Test job persistence and recovery"""
        # Create first queue and add jobs
        queue1 = InMemoryJobQueue(backup_file=temp_backup_file)
        job = Job(
            id="persist-job",
            type="test_task",
            payload={"data": "persist_test"}
        )
        await queue1.enqueue(job)
        
        # Create second queue and restore from backup
        queue2 = InMemoryJobQueue(backup_file=temp_backup_file)
        await queue2.restore_from_disk()
        
        # Check if job was restored
        restored_job = await queue2.get_job_status("persist-job")
        assert restored_job is not None
        assert restored_job.payload == {"data": "persist_test"}
        assert restored_job.status == JobStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_cleanup_completed_jobs(self, job_queue):
        """Test cleanup of old completed jobs"""
        # Create and complete some jobs
        for i in range(3):
            job = Job(
                id=f"cleanup-job-{i}",
                type="test_task",
                payload={"data": f"test{i}"}
            )
            await job_queue.enqueue(job)
            
            # Complete the job
            await job_queue.update_job_status(job.id, JobStatus.COMPLETED)
        
        # Check initial count
        stats = await job_queue.get_queue_stats()
        assert stats["total_jobs"] == 3
        assert stats["completed_jobs"] == 3
        
        # Cleanup completed jobs
        cleaned_count = await job_queue.cleanup_completed_jobs(max_age_hours=0)
        assert cleaned_count == 3
        
        # Check final count
        stats = await job_queue.get_queue_stats()
        assert stats["total_jobs"] == 0
        assert stats["completed_jobs"] == 0


@pytest.mark.asyncio
async def test_message_to_job_conversion():
    """Test Message to Job conversion"""
    message = Message(
        type="test_message",
        payload={"data": "test"},
        correlation_id="corr-123"
    )
    
    job = message.to_job(priority=JobPriority.HIGH)
    
    assert job.type == "test_message"
    assert job.payload == {"data": "test"}
    assert job.priority == JobPriority.HIGH
    assert job.metadata["correlation_id"] == "corr-123"
    assert job.status == JobStatus.PENDING
