

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
            
        task_data = await self.db.get_task(task_id)
        if not task_data:
            return None
        return Task.from_dict(task_data)

    async def create(self, task: Task) -> Task:
        """Create a new task and return the created task"""
        success = await self.db.store_task(task.to_dict())
        if not success:
            raise RuntimeError(f"Failed to create task '{task.name}'")
        return task

    async def list(self, is_active: Optional[bool] = None) -> List[Task]:
        tasks = await self.db.get_tasks(is_active=is_active)
        return [Task.from_dict(t) for t in tasks]

    async def update(self, task_id: str, task: Task) -> bool:
        task.update_timestamp()
        return await self.db.update_task(task_id, task.to_dict())

    async def delete(self, task_id: str) -> bool:
        return await self.db.delete_task(task_id)

    async def query(self, **kwargs) -> List[Task]:
        # Not implemented in storage, so just a stub for now
        raise NotImplementedError("Query is not implemented in StorageBackend.")
    

