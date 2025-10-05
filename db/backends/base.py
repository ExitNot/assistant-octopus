"""Storage backend abstract base definitions.

This module defines small, per-entity storage abstractions (CRUD-like)
so backend implementers can provide storage for only the entities they care about.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class EntityStore(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def list(self, **filters) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass


class JobStore(EntityStore):
    """CRUD for jobs"""
    pass


class TaskStore(EntityStore):
    """CRUD for tasks"""
    pass


class UserStore(EntityStore):
    """CRUD for users"""
    pass


class WhitelistStore(EntityStore):
    """CRUD for whitelist entries"""
    pass


class SessionStore(EntityStore):
    """CRUD for sessions"""
    pass


class HistoryStore(EntityStore):
    """CRUD for conversation history entries"""
    pass


class SessionStateStore(EntityStore):
    """CRUD for ADK session state"""
    pass


class StorageBackend(ABC):
    """Composite storage backend exposing per-entity stores as attributes."""

    @property
    @abstractmethod
    def jobs(self) -> JobStore:
        pass

    @property
    @abstractmethod
    def tasks(self) -> TaskStore:
        pass

    @property
    @abstractmethod
    def users(self) -> UserStore:
        pass

    @property
    @abstractmethod
    def whitelist(self) -> WhitelistStore:
        pass

    @property
    @abstractmethod
    def sessions(self) -> SessionStore:
        pass

    @property
    @abstractmethod
    def history(self) -> HistoryStore:
        pass

    @property
    @abstractmethod
    def session_state(self) -> SessionStateStore:
        pass
