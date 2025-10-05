

from typing import Optional, List
from db.storage import StorageBackend
from models.task_models import Task


class TaskRepo:

    def __init__(self, db_storage: StorageBackend) -> None:
        self.db = db_storage

    async def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        if not task_id:
            return None

        task_data = await self.db.tasks.get(task_id)
        if not task_data:
            return None
        return Task.from_dict(task_data)

    async def create(self, task: Task) -> Task:
        """Create a new task and return the created task"""
        result = await self.db.tasks.create(task.to_dict())
        if not result:
            raise RuntimeError(f"Failed to create task '{task.name}'")
        if isinstance(result, dict):
            return Task.from_dict(result)
        return task

    async def list(self, is_active: Optional[bool] = None) -> List[Task]:
        tasks = await self.db.tasks.list(is_active=is_active)
        return [Task.from_dict(t) for t in tasks]

    async def update(self, task_id: str, task: Task) -> bool:
        task.update_timestamp()
        updated = await self.db.tasks.update(task_id, task.to_dict())
        return updated is not None

    async def delete(self, task_id: str) -> bool:
        return await self.db.tasks.delete(task_id)

    async def query(self, **kwargs) -> List[Task]:
        # Not implemented in storage, so just a stub for now
        raise NotImplementedError("Query is not implemented in StorageBackend.")


