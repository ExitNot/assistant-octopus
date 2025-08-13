# ADR-02: Scheduler Service Architecture

## Status
Proposed

## Context
The Assistant-Octopus system needs a robust scheduling service to handle:
- **Scheduled Tasks**: One-time tasks executed at specific dates/times
- **Repeated Tasks**: Recurring tasks with configurable intervals (daily, weekly, monthly, custom)
- **Task Management**: Full CRUD operations for creating, reading, updating, and deleting tasks
- **Task Execution**: Reliable execution of tasks by integrating with the Messaging Service (ADR-01)

The system must provide a clean, RESTful API for task management while being designed to scale from a single-container deployment to a multi-service architecture, maintaining clean separation of concerns and testability.

## Decision
Implement a **Service-Oriented Module Architecture** that integrates with the **Messaging Service (ADR-01)** for task execution, using **Abstract Communication Layer** that allows seamless migration from single-container to multi-container deployment.

### Core Principles
1. **Dependency Injection**: All services receive their dependencies through constructor injection
2. **Abstract Interfaces**: Communication between services uses abstract interfaces (e.g., `JobQueue` from ADR-01)
3. **Implementation Swapping**: Easy to switch between in-memory and external implementations
4. **Single Process First**: Start with all services in one process, migrate to separate processes later
5. **Messaging Integration**: Leverage the Messaging Service for reliable task execution

## Architecture Overview

### Service Structure
```
/app
├── services/
│   ├── messaging/                 # Messaging Service Package (ADR-01)
│   ├── scheduler/                 # Scheduler Service Package
│   │   ├── __init__.py           # Package exports
│   │   ├── task_service.py       # Task CRUD operations
│   │   └── scheduler_service.py  # Task scheduling and execution
│   ├── llm/                       # LLM Service Package
│   ├── supervisor/                # Supervisor Service Package
│   ├── __init__.py                # Main services package
│   └── api.py                     # API entry point
├── api/
│   ├── routes/
│   │   └── tasks.py              # Task management endpoints
│   └── models/
│       └── task_models.py        # Task request/response models
├── shared/
│   ├── models.py                  # Shared data models
│   └── config.py                  # Configuration
└── main.py                        # Application entry point
```

### Key Components

#### 1. Task Models
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class TaskType(Enum):
    SCHEDULED = "scheduled"      # One-time task
    REPEATED = "repeated"        # Recurring task

class RepeatInterval(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"            # Custom cron expression

@dataclass
class Task:
    id: str
    name: str
    description: Optional[str]
    task_type: TaskType
    payload: Dict[str, Any]
    scheduled_at: datetime
    repeat_interval: Optional[RepeatInterval] = None
    cron_expression: Optional[str] = None  # For custom intervals
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
```

#### 2. Task Service
```python
from typing import List, Optional
from datetime import datetime

class TaskService:
    def __init__(self, scheduler_service: SchedulerService):
        self.scheduler_service = scheduler_service
    
    async def create_task(self, task: Task) -> Task:
        """Create a new scheduled or repeated task"""
        # Validate task data
        # Store task in database
        # Schedule job(s) in scheduler
        return task
    
    async def get_tasks(self, 
                        task_type: Optional[TaskType] = None,
                        is_active: Optional[bool] = None) -> List[Task]:
        """Get list of tasks with optional filtering"""
        pass
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a specific task by ID"""
        pass
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Optional[Task]:
        """Update an existing task"""
        # Update task data
        # Reschedule if timing changed
        pass
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task and cancel all related jobs"""
        # Cancel scheduled jobs
        # Remove from database
        pass
```

#### 3. Scheduler Service
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.triggers.cron import CronTrigger
from services.messaging import MessagingService, Job, JobPriority

class SchedulerService:
    def __init__(self, messaging_service: MessagingService, llm_service: LLMService):
        self.messaging_service = messaging_service
        self.llm_service = llm_service
        
        # Configure scheduler with configurable backend
        jobstores = {
            'default': MemoryJobStore()  # Switch to RedisJobStore later
        }
        self.scheduler = AsyncIOScheduler(jobstores=jobstores)

    async def start(self):
        self.scheduler.start()
        # No need for separate job processing - Messaging Service handles it

    async def schedule_task(self, task: Task) -> None:
        """Schedule a task based on its type and timing"""
        if task.task_type == TaskType.SCHEDULED:
            self.scheduler.add_job(
                self._execute_task,
                'date',
                run_date=task.scheduled_at,
                args=[task.id],
                id=f"task_{task.id}"
            )
        elif task.task_type == TaskType.REPEATED:
            if task.repeat_interval == RepeatInterval.CUSTOM:
                self.scheduler.add_job(
                    self._execute_task,
                    CronTrigger.from_crontab(task.cron_expression),
                    args=[task.id],
                    id=f"task_{task.id}"
                )
            else:
                # Handle standard intervals
                self._schedule_recurring_task(task)

    def _schedule_recurring_task(self, task: Task):
        """Schedule a recurring task with standard intervals"""
        if task.repeat_interval == RepeatInterval.DAILY:
            self.scheduler.add_job(
                self._execute_task,
                'cron',
                hour=task.scheduled_at.hour,
                minute=task.scheduled_at.minute,
                args=[task.id],
                id=f"task_{task.id}"
            )
        elif task.repeat_interval == RepeatInterval.WEEKLY:
            self.scheduler.add_job(
                self._execute_task,
                'cron',
                day_of_week=task.scheduled_at.weekday(),
                hour=task.scheduled_at.hour,
                minute=task.scheduled_at.minute,
                args=[task.id],
                id=f"task_{task.id}"
            )
        elif task.repeat_interval == RepeatInterval.MONTHLY:
            self.scheduler.add_job(
                self._execute_task,
                'cron',
                day=task.scheduled_at.day,
                hour=task.scheduled_at.hour,
                minute=task.scheduled_at.minute,
                args=[task.id],
                id=f"task_{task.id}"
            )

    async def _execute_task(self, task_id: str):
        """Execute a scheduled task by creating a job in the Messaging Service"""
        # Create job and enqueue it through the messaging service
        job = Job(
            type="scheduled_task",
            payload={"task_id": task_id},
            scheduled_at=datetime.now(),
            priority=JobPriority.NORMAL
        )
        
        # Send the job through the messaging service
        await self.messaging_service.send_message(
            Message(
                type="scheduled_task",
                payload={"task_id": task_id},
                correlation_id=f"task_{task_id}"
            )
        )

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        try:
            self.scheduler.remove_job(f"task_{task_id}")
            return True
        except Exception:
            return False

    async def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task"""
        try:
            self.scheduler.pause_job(f"task_{task_id}")
            return True
        except Exception:
            return False

    async def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        try:
            self.scheduler.resume_job(f"task_{task_id}")
            return True
        except Exception:
            return False
```

## API Design

### Task Management Endpoints

#### 1. Create Task
```http
POST /api/v1/tasks
Content-Type: application/json

{
  "name": "Daily reminder",
  "description": "Send daily reminder message",
  "task_type": "repeated",
  "payload": {
    "message": "Time for your daily check-in!",
    "chat_id": "123456789"
  },
  "scheduled_at": "2024-01-15T09:00:00Z",
  "repeat_interval": "daily"
}
```

#### 2. List Tasks
```http
GET /api/v1/tasks?task_type=repeated&is_active=true
GET /api/v1/tasks?task_type=scheduled
GET /api/v1/tasks
```

#### 3. Get Task
```http
GET /api/v1/tasks/{task_id}
```

#### 4. Update Task
```http
PUT /api/v1/tasks/{task_id}
Content-Type: application/json

{
  "name": "Updated reminder name",
  "scheduled_at": "2024-01-16T10:00:00Z"
}
```

#### 5. Delete Task
```http
DELETE /api/v1/tasks/{task_id}
```

#### 6. Task Control
```http
POST /api/v1/tasks/{task_id}/pause
POST /api/v1/tasks/{task_id}/resume
POST /api/v1/tasks/{task_id}/cancel
```

### Task Models

#### Request Models
```python
class CreateTaskRequest(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: TaskType
    payload: Dict[str, Any]
    scheduled_at: datetime
    repeat_interval: Optional[RepeatInterval] = None
    cron_expression: Optional[str] = None

class UpdateTaskRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    repeat_interval: Optional[RepeatInterval] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None
```

#### Response Models
```python
class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    task_type: TaskType
    payload: Dict[str, Any]
    scheduled_at: datetime
    repeat_interval: Optional[RepeatInterval]
    cron_expression: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    page: int
    size: int
```

## Technology Stack

### Core Libraries
- **FastAPI**: Web framework (lightweight, async, easy containerization)
- **APScheduler**: Flexible scheduler (supports in-memory and persistent backends)
- **asyncio**: For concurrent handling
- **Pydantic**: Data validation and settings management

### Integration Points
- **Messaging Service (ADR-01)**: For reliable task execution and job management
- **Job Queue**: Shared interface for communication between services

## Implementation Plan

### Phase 1: Single Container (Weeks 1-2)
**Goal**: Get basic scheduling working with Messaging Service integration

#### Tasks
1. **Create Core Models and Interfaces** (Week 1)
   - [ ] Define `Task` data models
   - [ ] Create `TaskType` and `RepeatInterval` enums
   - [ ] Integrate with Messaging Service models from ADR-01

2. **Implement Task Management Service** (Week 1-2)
   - [ ] Create `TaskService` with full CRUD operations
   - [ ] Implement task validation and business logic
   - [ ] Add task filtering and pagination

3. **Implement Scheduler Service** (Week 1-2)
   - [ ] Create `SchedulerService` with APScheduler
   - [ ] Implement task scheduling for both one-time and recurring tasks
   - [ ] Add support for custom cron expressions
   - [ ] Integrate with Messaging Service for job execution

4. **Create REST API** (Week 2)
   - [ ] Implement task management endpoints
   - [ ] Add request/response models with Pydantic
   - [ ] Implement proper error handling and validation
   - [ ] Add API documentation with OpenAPI/Swagger

5. **Integration and Testing** (Week 2)
   - [ ] Integrate with Messaging Service (ADR-01)
   - [ ] Add configuration management
   - [ ] Create comprehensive tests for all endpoints
   - [ ] Add basic health checks

#### Configuration
```yaml
# docker-compose.yml
services:
  assistant:
    build: .
    environment:
      - MESSAGING_WORKERS=3
      - SCHEDULER_BACKEND=memory
```

### Phase 2: Multi-Container (Weeks 3-4)
**Goal**: Separate services for better scalability and fault tolerance

#### Tasks
1. **Service Separation** (Week 3-4)
   - [ ] Extract services to separate containers
   - [ ] Update configuration management
   - [ ] Add inter-service communication
   - [ ] Implement task synchronization between services

#### Configuration
```yaml
# docker-compose.yml
services:
  telegram-service:
    build: .
    command: python -m services.telegram_service
    environment:
      - MESSAGING_WORKERS=2
  
  scheduler-service:
    build: .
    command: python -m services.scheduler_service
    environment:
      - MESSAGING_WORKERS=1
      - SCHEDULER_BACKEND=redis
  
  messaging-service:
    build: .
    command: python -m services.messaging_service
    environment:
      - MESSAGING_WORKERS=3
  
  redis:
    image: redis:alpine
```

## Configuration Management

```python
# shared/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Scheduler Configuration
    scheduler_backend: str = "memory"  # or "redis"
    scheduler_timezone: str = "UTC"
    
    # Messaging Service Integration (from ADR-01)
    messaging_workers: int = 3
    messaging_backup_file: str = "jobs_backup.json"
    
    class Config:
        env_file = ".env"
```

## Benefits

✅ **Messaging Integration** - Leverages robust job processing from ADR-01
✅ **Single container deployment now** - Quick to get started
✅ **Easy migration to multi-container** - No code changes needed
✅ **Clean separation of concerns** - Each service has a single responsibility
✅ **Testable components** - Easy to mock dependencies
✅ **Minimal overhead initially** - Start simple, scale as needed
✅ **Full CRUD API** - Complete task management capabilities
✅ **Flexible scheduling** - Support for one-time and recurring tasks
✅ **Custom intervals** - Cron expression support for complex schedules
✅ **Task Control** - Pause, resume, and cancel capabilities

## Risks and Mitigation

### Risks
1. **Complexity**: Abstract interfaces add initial complexity
2. **Dependencies**: Tight coupling with Messaging Service
3. **Migration**: Moving to multi-container requires careful testing

### Mitigation
1. **Start Simple**: Begin with concrete implementations, add abstractions gradually
2. **Interface Design**: Use well-defined interfaces for loose coupling
3. **Testing**: Comprehensive testing before migration

## Alternatives Considered

1. **Direct Job Creation**: Scheduler directly creates jobs without Messaging Service
   - ❌ Duplicates job management logic
   - ❌ Less reliable execution

2. **Event-Driven Architecture**: Using message brokers from start
   - ❌ Additional infrastructure complexity
   - ❌ Harder to debug and test

3. **Monolithic Scheduler**: All logic in one service
   - ❌ Harder to scale and test
   - ❌ Difficult to deploy independently

## Conclusion

The Service-Oriented Module Architecture with Messaging Service Integration provides the best balance of:
- **Simplicity**: Easy to understand and implement
- **Reliability**: Leverages robust job processing from Messaging Service
- **Flexibility**: Can adapt to changing requirements
- **Scalability**: Clear path from single to multi-container
- **Maintainability**: Clean separation of concerns
- **API Completeness**: Full CRUD operations for task management
- **Scheduling Power**: Support for both simple and complex scheduling patterns

This approach follows the principle of "make it work, make it right, make it fast" while ensuring the architecture can evolve with the system's needs. The integration with the Messaging Service (ADR-01) provides reliable task execution while maintaining the architectural flexibility to scale and evolve.
