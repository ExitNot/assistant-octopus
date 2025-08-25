"""
Tests for Messaging Service Models

Tests the Job and Message models including serialization,
deserialization, and state transitions.
"""

import pytest
from datetime import datetime
from models.messaging_models import Job, Message, JobStatus, JobPriority

class TestJob:
    """Test Job model functionality"""
    
    def test_job_creation_with_defaults(self):
        """Test job creation with minimal required fields"""
        job = Job(
            id="test-123",
            type="test_job",
            payload={"key": "value"}
        )
        
        assert job.id == "test-123"
        assert job.type == "test_job"
        assert job.payload == {"key": "value"}
        assert job.priority == JobPriority.NORMAL
        assert job.status == JobStatus.PENDING
        assert job.retry_count == 0
        assert job.max_retries == 3
        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None
    
    def test_job_creation_with_all_fields(self):
        """Test job creation with all fields specified"""
        now = datetime.now()
        job = Job(
            id="test-456",
            type="test_job",
            payload={"key": "value"},
            priority=JobPriority.HIGH,
            status=JobStatus.PENDING,
            created_at=now,
            scheduled_at=now,
            max_retries=5,
            metadata={"source": "test"}
        )
        
        assert job.id == "test-456"
        assert job.priority == JobPriority.HIGH
        assert job.max_retries == 5
        assert job.metadata == {"source": "test"}
    
    def test_job_auto_id_generation(self):
        """Test that job ID is auto-generated when not provided"""
        job = Job(
            type="test_job",
            payload={"key": "value"}
        )
        
        assert job.id is not None
        assert len(job.id) > 0
    
    def test_job_auto_timestamp_generation(self):
        """Test that created_at timestamp is auto-generated when not provided"""
        before = datetime.now()
        job = Job(
            id="test-789",
            type="test_job",
            payload={"key": "value"}
        )
        after = datetime.now()
        
        assert job.created_at is not None
        assert before <= job.created_at <= after
    
    def test_job_state_transitions(self):
        """Test job state transition methods"""
        job = Job(
            id="test-state",
            type="test_job",
            payload={"key": "value"}
        )
        
        # Test starting
        assert job.can_start()
        job.mark_started()
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        assert not job.can_start()
        
        # Test completion
        result = {"output": "success"}
        job.mark_completed(result)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result == result
    
    def test_job_failure_handling(self):
        """Test job failure and retry logic"""
        job = Job(
            id="test-failure",
            type="test_job",
            payload={"key": "value"},
            max_retries=2
        )
        
        # Test failure
        error_msg = "Something went wrong"
        job.mark_failed(error_msg)
        assert job.status == JobStatus.FAILED
        assert job.error == error_msg
        assert job.completed_at is not None
        
        # Test retry logic
        assert job.is_retryable()
        job.retry_count = 2
        assert not job.is_retryable()
        
        # Test cancellation
        job.mark_cancelled()
        assert job.status == JobStatus.CANCELLED
        assert not job.is_retryable()
    
    def test_job_serialization(self):
        """Test job serialization and deserialization"""
        original_job = Job(
            id="test-serialization",
            type="test_job",
            payload={"key": "value"},
            priority=JobPriority.HIGH,
            metadata={"source": "test"}
        )
        
        # Convert to dict
        job_dict = original_job.to_dict()
        
        # Convert back to job
        restored_job = Job.from_dict(job_dict)
        
        # Verify all fields are preserved
        assert restored_job.id == original_job.id
        assert restored_job.type == original_job.type
        assert restored_job.payload == original_job.payload
        assert restored_job.priority == original_job.priority
        assert restored_job.status == original_job.status
        assert restored_job.metadata == original_job.metadata


class TestMessage:
    """Test Message model functionality"""
    
    def test_message_creation_with_defaults(self):
        """Test message creation with minimal required fields"""
        message = Message(
            type="test_message",
            payload={"key": "value"}
        )
        
        assert message.type == "test_message"
        assert message.payload == {"key": "value"}
        assert message.timestamp is not None
        assert message.correlation_id is not None
    
    def test_message_creation_with_all_fields(self):
        """Test message creation with all fields specified"""
        now = datetime.now()
        message = Message(
            type="test_message",
            payload={"key": "value"},
            timestamp=now,
            correlation_id="corr-123"
        )
        
        assert message.timestamp == now
        assert message.correlation_id == "corr-123"
    
    def test_message_auto_timestamp_generation(self):
        """Test that timestamp is auto-generated when not provided"""
        before = datetime.now()
        message = Message(
            type="test_message",
            payload={"key": "value"}
        )
        after = datetime.now()
        
        assert message.timestamp is not None
        assert before <= message.timestamp <= after
    
    def test_message_auto_correlation_id_generation(self):
        """Test that correlation_id is auto-generated when not provided"""
        message = Message(
            type="test_message",
            payload={"key": "value"}
        )
        
        assert message.correlation_id is not None
        assert len(message.correlation_id) > 0
    
    def test_message_serialization(self):
        """Test message serialization and deserialization"""
        original_message = Message(
            type="test_message",
            payload={"key": "value"},
            correlation_id="corr-456"
        )
        
        # Convert to dict
        message_dict = original_message.to_dict()
        
        # Convert back to message
        restored_message = Message.from_dict(message_dict)
        
        # Verify all fields are preserved
        assert restored_message.type == original_message.type
        assert restored_message.payload == original_message.payload
        assert restored_message.correlation_id == original_message.correlation_id
    
    def test_message_to_job_conversion(self):
        """Test converting message to job"""
        message = Message(
            type="test_message",
            payload={"key": "value"},
            correlation_id="corr-789"
        )
        
        job = message.to_job(priority=JobPriority.HIGH)
        
        assert job.type == message.type
        assert job.payload == message.payload
        assert job.priority == JobPriority.HIGH
        assert job.metadata["correlation_id"] == message.correlation_id
        assert job.status == JobStatus.PENDING
