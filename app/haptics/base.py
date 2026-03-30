"""Base abstractions for haptic runtime backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class HapticBackendStatus(BaseModel):
    """Public status payload for a haptic backend."""

    backend: str
    backend_title: str | None = None
    connected: bool
    mode: str
    summary: str
    capabilities: list[str] = Field(default_factory=list)


class HapticBackend(ABC):
    """Abstract runtime haptic backend."""

    @abstractmethod
    def start(self) -> None:
        """Start or initialize the backend."""

    @abstractmethod
    def stop(self) -> None:
        """Stop or release the backend."""

    @abstractmethod
    def status(self) -> HapticBackendStatus:
        """Return the current backend status."""
