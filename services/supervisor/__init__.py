"""
Supervisor Service Package

Handles high-level task coordination and user interaction.
"""

from .supervisor_router import supervisor_router

__all__ = [
    "supervisor_router"
]
