import asyncio
import contextvars
from typing import Any, Dict, Optional

# Context variable to track the current active job ID
active_job_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "active_job_id",
    default=None,
)


class EventBus:
    _queues: Dict[str, asyncio.Queue] = {}

    @classmethod
    async def subscribe(cls, job_id: str) -> asyncio.Queue:
        if job_id not in cls._queues:
            cls._queues[job_id] = asyncio.Queue()

        return cls._queues[job_id]

    @classmethod
    async def publish(
        cls,
        event_type: str,
        data: Any,
        job_id: Optional[str] = None,
    ) -> None:
        target_job_id = job_id or active_job_id.get()

        if target_job_id and target_job_id in cls._queues:
            await cls._queues[target_job_id].put(
                {
                    "event": event_type,
                    "data": data,
                }
            )

    @classmethod
    def publish_sync(
        cls,
        event_type: str,
        data: Any,
        job_id: Optional[str] = None,
    ) -> None:
        target_job_id = job_id or active_job_id.get()

        if target_job_id and target_job_id in cls._queues:
            try:
                cls._queues[target_job_id].put_nowait(
                    {
                        "event": event_type,
                        "data": data,
                    }
                )
            except asyncio.QueueFull:
                pass

    @classmethod
    def unsubscribe(cls, job_id: str) -> None:
        if job_id in cls._queues:
            del cls._queues[job_id]
