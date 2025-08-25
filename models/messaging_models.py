"""
Job and Message Models for Messaging Service

This module defines the core data structures for the messaging service,
including job status tracking, priority levels, and message handling.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid


class JobStatus(Enum):
    """Job status enumeration for tracking job lifecycle"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority levels for queue ordering"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Job:
    """
    Job representation for asynchronous task processing
    
    Attributes:
        id: Unique identifier for the job
        type: Type/category of the job for routing
        payload: Job-specific data and parameters
        priority: Job priority level for queue ordering
        status: Current status of the job
        created_at: Timestamp when job was created
        scheduled_at: Optional scheduled execution time
        started_at: Timestamp when job execution began
        completed_at: Timestamp when job completed/failed
        result: Job execution result data
        error: Error message if job failed
        retry_count: Number of retry attempts made
        max_retries: Maximum number of retry attempts allowed
        metadata: Additional job metadata
    """
    id: Optional[str] = None
    type: str = None
    payload: Dict[str, Any] = None
    priority: JobPriority = JobPriority.NORMAL
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values after object creation"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization"""
        data = asdict(self)
        # Convert enum values to their string representations
        if isinstance(data.get('status'), JobStatus):
            data['status'] = data['status'].value
        if isinstance(data.get('priority'), JobPriority):
            data['priority'] = data['priority'].value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary data"""
        # Convert string representations back to proper types
        if isinstance(data.get('status'), str):
            data['status'] = JobStatus(data['status'])
        if isinstance(data.get('priority'), str):
            data['priority'] = JobPriority(data['priority'])
        
        # Convert datetime strings back to datetime objects
        for field in ['created_at', 'scheduled_at', 'started_at', 'completed_at']:
            if isinstance(data.get(field), str):
                data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def is_retryable(self) -> bool:
        """Check if job can be retried"""
        return self.retry_count < self.max_retries and self.status != JobStatus.CANCELLED
    
    def can_start(self) -> bool:
        """Check if job can start execution"""
        return self.status == JobStatus.PENDING
    
    def mark_started(self):
        """Mark job as started"""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now()
    
    def mark_completed(self, result: Optional[Dict[str, Any]] = None):
        """Mark job as completed successfully"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        if result is not None:
            self.result = result
    
    def mark_failed(self, error: str):
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.error = error
    
    def mark_cancelled(self):
        """Mark job as cancelled"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now()


@dataclass
class Message:
    """
    Message representation for inter-service communication
    
    Attributes:
        type: Type/category of the message
        payload: Message data and parameters
        timestamp: When the message was created
        correlation_id: Optional correlation ID for tracking
    """
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = None
    correlation_id: Optional[str] = None

    def __post_init__(self):
        """Initialize default values after object creation"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.correlation_id is None:
            self.correlation_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary data"""
        # Convert datetime string back to datetime object
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        
        return cls(**data)
    
    def to_job(self, priority: JobPriority = JobPriority.NORMAL) -> Job:
        """Convert message to a job for processing"""
        return Job(
            id=str(uuid.uuid4()),
            type=self.type,
            payload=self.payload,
            priority=priority,
            metadata={"correlation_id": self.correlation_id}
        )
