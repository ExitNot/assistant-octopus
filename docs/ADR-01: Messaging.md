# ADR-01: Messaging Service Architecture

## Status
Proposed

## Context
The Assistant-Octopus system needs a messaging service to handle asynchronous task processing within the same container. This service must:

- **Process Async Tasks**: Handle long-running LLM requests, scheduled tasks, and other asynchronous operations
- **Job Queue Management**: Provide reliable job queuing with status tracking and persistence
- <del>**Worker Pool**: Support multiple concurrent workers for parallel task processing~</del>
- **Fault Tolerance**: Handle failures gracefully with retry mechanisms and job recovery
- **Integration**: Work seamlessly with the Scheduler Service (ADR-02) and other system components

The messaging service should be lightweight, easy to debug, and provide a foundation for future scaling without requiring external dependencies initially.

## Decision
Implement a **Single-Container Messaging Service** using **Enhanced AsyncIO Queues** with **Persistent Job Storage** and **Worker Pool Management**.

### Core Principles
1. **Container Co-location**: All messaging components run in the same container as other services
2. **AsyncIO Foundation**: Use Python's built-in asyncio for efficient concurrent processing
3. **Job Persistence**: Simple file-based persistence to survive container restarts
4. **Worker Pool**: Configurable number of concurrent workers for parallel processing
5. **Status Tracking**: Comprehensive job lifecycle management (pending, running, completed, failed)

## Architecture Overview

### Service Structure
```
/app
├── services/
│   ├── messaging/                 # Messaging Service Package
│   │   ├── __init__.py           # Package exports
│   │   ├── models.py             # Job and message models
│   │   ├── job_queue.py          # Job queue implementation
│   │   ├── worker_pool.py        # Worker pool management
│   │   └── messaging_service.py  # Core messaging service
│   ├── scheduler/                 # Scheduler Service Package
│   ├── llm/                       # LLM Service Package
│   ├── supervisor/                # Supervisor Service Package
│   ├── __init__.py                # Main services package
│   └── api.py                     # API entry point
├── shared/
│   ├── models.py                  # Shared data models
│   └── config.py                  # Configuration
└── main.py                        # Application entry point
```

### Key Components

#### 1. Job and Message Models
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Job:
    id: str
    type: str
    payload: Dict[str, Any]
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
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.id is None:
            self.id = str(uuid.uuid4())

@dataclass
class Message:
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = None
    correlation_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
```

#### 2. Job Queue Interface
```python
class JobQueue(ABC):
    @abstractmethod
    async def enqueue(self, job: Job) -> None: pass
    
    @abstractmethod
    async def dequeue(self, priority: bool = True) -> Optional[Job]: pass
    
    @abstractmethod
    async def get_job_status(self, job_id: str) -> Optional[Job]: pass
    
    @abstractmethod
    async def update_job_status(self, job_id: str, status: JobStatus, **kwargs) -> bool: pass
    
    @abstractmethod
    async def get_jobs_by_status(self, status: JobStatus) -> List[Job]: pass
    
    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool: pass
```

#### 3. In-Memory Job Queue Implementation
```python
import asyncio
import json
import aiofiles
from typing import Dict, List, Optional
from datetime import datetime

class InMemoryJobQueue(JobQueue):
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
        
    async def enqueue(self, job: Job) -> None:
        async with self._lock:
            self._jobs[job.id] = job
            await self._queues[job.priority].put(job)
            await self._backup_to_disk()
    
    async def dequeue(self, priority: bool = True) -> Optional[Job]:
        if priority:
            # Process higher priority queues first
            for priority_level in [JobPriority.URGENT, JobPriority.HIGH, 
                                 JobPriority.NORMAL, JobPriority.LOW]:
                if not self._queues[priority_level].empty():
                    job = await self._queues[priority_level].get()
                    await self.update_job_status(job.id, JobStatus.RUNNING)
                    return job
        else:
            # Round-robin across all queues
            for _ in range(sum(q.qsize() for q in self._queues.values())):
                for priority_level in [JobPriority.URGENT, JobPriority.HIGH, 
                                     JobPriority.NORMAL, JobPriority.LOW]:
                    if not self._queues[priority_level].empty():
                        job = await self._queues[priority_level].get()
                        await self.update_job_status(job.id, JobStatus.RUNNING)
                        return job
        return None
    
    async def get_job_status(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)
    
    async def update_job_status(self, job_id: str, status: JobStatus, **kwargs) -> bool:
        if job_id not in self._jobs:
            return False
        
        job = self._jobs[job_id]
        job.status = status
        
        # Update additional fields
        if status == JobStatus.RUNNING and 'started_at' not in kwargs:
            job.started_at = datetime.now()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED] and 'completed_at' not in kwargs:
            job.completed_at = datetime.now()
        
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        
        await self._backup_to_disk()
        return True
    
    async def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        return [job for job in self._jobs.values() if job.status == status]
    
    async def cancel_job(self, job_id: str) -> bool:
        if job_id not in self._jobs:
            return False
        
        job = self._jobs[job_id]
        if job.status == JobStatus.PENDING:
            # Remove from queue (this is simplified - in practice you'd need to track queue positions)
            job.status = JobStatus.CANCELLED
            await self._backup_to_disk()
            return True
        return False
    
    async def _backup_to_disk(self):
        """Persist jobs to disk for container restart recovery"""
        try:
            backup_data = {
                "jobs": {k: asdict(v) for k, v in self._jobs.items()},
                "timestamp": datetime.now().isoformat()
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
                    for job_id, job_data in backup_data.get("jobs", {}).items():
                        # Convert datetime strings back to datetime objects
                        for field in ['created_at', 'scheduled_at', 'started_at', 'completed_at']:
                            if job_data.get(field):
                                job_data[field] = datetime.fromisoformat(job_data[field])
                        
                        # Convert enum fields
                        job_data['status'] = JobStatus(job_data['status'])
                        job_data['priority'] = JobPriority(job_data['priority'])
                        
                        job = Job(**job_data)
                        self._jobs[job_id] = job
                        
                        # Re-queue pending jobs
                        if job.status == JobStatus.PENDING:
                            await self._queues[job.priority].put(job)
        except FileNotFoundError:
            # No backup file exists yet
            pass
        except Exception as e:
            print(f"Failed to restore jobs: {e}")
```

#### 4. Worker Pool Management
```python
import asyncio
from typing import Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor

class WorkerPool:
    def __init__(self, job_queue: JobQueue, num_workers: int = 3):
        self.job_queue = job_queue
        self.num_workers = num_workers
        self.workers: List[asyncio.Task] = []
        self.processors: Dict[str, Callable] = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=num_workers)
        self.is_running = False
    
    def register_processor(self, job_type: str, processor: Callable):
        """Register a processor function for a specific job type"""
        self.processors[job_type] = processor
    
    async def start(self):
        """Start the worker pool"""
        if self.is_running:
            return
        
        self.is_running = True
        self.workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.num_workers)
        ]
        
        # Start recovery process for any jobs that were running before restart
        await self.job_queue.restore_from_disk()
        
        # Re-queue any jobs that were running before restart
        running_jobs = await self.job_queue.get_jobs_by_status(JobStatus.RUNNING)
        for job in running_jobs:
            await self.job_queue.update_job_status(job.id, JobStatus.PENDING)
            # Re-queue with original priority
            await self.job_queue.enqueue(job)
    
    async def stop(self):
        """Stop the worker pool gracefully"""
        self.is_running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for all workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
    
    async def _worker(self, worker_name: str):
        """Individual worker process"""
        while self.is_running:
            try:
                # Get next job
                job = await self.job_queue.dequeue()
                if not job:
                    await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                    continue
                
                print(f"{worker_name} processing job {job.id} of type {job.type}")
                
                # Process the job
                try:
                    if job.type in self.processors:
                        processor = self.processors[job.type]
                        
                        # Check if processor is async or sync
                        if asyncio.iscoroutinefunction(processor):
                            result = await processor(job.payload)
                        else:
                            # Run sync processor in thread pool
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(
                                self.thread_pool, processor, job.payload
                            )
                        
                        await self.job_queue.update_job_status(
                            job.id, JobStatus.COMPLETED, result=result
                        )
                        print(f"{worker_name} completed job {job.id}")
                        
                    else:
                        error_msg = f"No processor registered for job type: {job.type}"
                        await self.job_queue.update_job_status(
                            job.id, JobStatus.FAILED, error=error_msg
                        )
                        print(f"{worker_name} failed job {job.id}: {error_msg}")
                
                except Exception as e:
                    error_msg = str(e)
                    print(f"{worker_name} failed job {job.id}: {error_msg}")
                    
                    # Handle retries
                    if job.retry_count < job.max_retries:
                        job.retry_count += 1
                        await self.job_queue.update_job_status(
                            job.id, JobStatus.PENDING, retry_count=job.retry_count
                        )
                        # Re-queue for retry
                        await self.job_queue.enqueue(job)
                    else:
                        await self.job_queue.update_job_status(
                            job.id, JobStatus.FAILED, error=error_msg
                        )
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"{worker_name} encountered error: {e}")
                await asyncio.sleep(1)  # Brief pause before continuing
```

#### 5. Messaging Service
```python
class MessagingService:
    def __init__(self, job_queue: JobQueue, worker_pool: WorkerPool):
        self.job_queue = job_queue
        self.worker_pool = worker_pool
        self.message_handlers: Dict[str, Callable] = {}
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler
    
    async def send_message(self, message: Message) -> str:
        """Send a message and return the job ID"""
        # Convert message to job
        job = Job(
            type=message.type,
            payload=message.payload,
            metadata={"correlation_id": message.correlation_id}
        )
        
        await self.job_queue.enqueue(job)
        return job.id
    
    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get the status of a specific job"""
        return await self.job_queue.get_job_status(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job"""
        return await self.job_queue.cancel_job(job_id)
    
    async def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """Get all jobs with a specific status"""
        return await self.job_queue.get_jobs_by_status(status)
    
    async def start(self):
        """Start the messaging service"""
        await self.worker_pool.start()
    
    async def stop(self):
        """Stop the messaging service"""
        await self.worker_pool.stop()
```

## Integration with Scheduler Service

The Messaging Service integrates with the Scheduler Service (ADR-02) through the shared `JobQueue` interface:

```python
# In services/scheduler/scheduler_service.py
class SchedulerService:
    def __init__(self, messaging_service: MessagingService, llm_service: LLMService):
        self.messaging_service = messaging_service
        self.llm_service = llm_service
        # ... rest of implementation

    async def _execute_task(self, task_id: str):
        """Execute a scheduled task by creating a job"""
        job = Job(
            type="scheduled_task",
            payload={"task_id": task_id},
            scheduled_at=datetime.now()
        )
        await self.messaging_service.send_message(
            Message(
                type="scheduled_task",
                payload={"task_id": task_id},
                correlation_id=f"task_{task_id}"
            )
        )
```

## Configuration

```python
# shared/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Messaging Service Configuration
    messaging_workers: int = 3
    messaging_backup_file: str = "jobs_backup.json"
    messaging_max_retries: int = 3
    
    # Job Queue Configuration
    job_queue_priority_enabled: bool = True
    job_queue_backup_interval: int = 60  # seconds
    
    class Config:
        env_file = ".env"
```

## Benefits

✅ **Zero External Dependencies** - Uses only Python standard library and asyncio
✅ **Container Co-location** - Runs in same container as other services
✅ **Job Persistence** - Survives container restarts with file-based backup
✅ **Priority Queuing** - Supports different job priority levels
✅ **Worker Pool** - Configurable number of concurrent workers
✅ **Fault Tolerance** - Automatic retry mechanism and error handling
✅ **Easy Debugging** - Simple in-memory implementation for development
✅ **Future Ready** - Easy to migrate to external queue systems later

## Risks and Mitigation

### Risks
1. **Memory Usage**: In-memory storage may consume significant memory with many jobs
2. **Data Loss**: File-based persistence could be lost if container storage is ephemeral
3. **Scalability**: Single-container approach may not handle very high load

### Mitigation
1. **Memory Management**: Implement job cleanup and archiving for old completed jobs
2. **Persistence**: Use volume mounts for persistent storage in production
3. **Monitoring**: Add metrics to identify when to migrate to external systems

## Implementation Plan

### Phase 1: Core Implementation (Week 1)
- [ ] Implement `Job` and `Message` models
- [ ] Create `JobQueue` interface and `InMemoryJobQueue` implementation
- [ ] Implement basic job persistence and recovery
- [ ] Add priority queuing support

### Phase 2: Worker Pool (Week 1-2)
- [ ] Implement `WorkerPool` with configurable workers
- [ ] Add job processor registration system
- [ ] Implement retry mechanism and error handling
- [ ] Add graceful shutdown capabilities

### Phase 3: Integration (Week 2)
- [ ] Create `MessagingService` facade
- [ ] Integrate with existing services
- [ ] Add configuration management
- [ ] Implement health checks and monitoring

## Conclusion

The Single-Container Messaging Service with Enhanced AsyncIO Queues provides an excellent foundation for handling asynchronous tasks in the Assistant-Octopus system. It offers:

- **Simplicity**: Easy to understand and debug
- **Reliability**: Job persistence and recovery mechanisms
- **Performance**: Efficient concurrent processing with worker pools
- **Flexibility**: Easy to extend and modify
- **Integration**: Seamless integration with the Scheduler Service

This approach follows the principle of starting simple while building a solid foundation for future scaling. The service can easily evolve to use external queue systems (Redis, RabbitMQ, etc.) when needed, without requiring changes to the consuming services.