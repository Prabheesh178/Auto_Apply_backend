import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity_log import ActivityLog
from app.database import AsyncSessionLocal

class ActivityService:
    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def log(self, level: str, component: str, message: str, metadata: Dict[str, Any] = None):
        if metadata is None:
            metadata = {}
            
        timestamp = datetime.utcnow()
        payload = {
            "level": level,
            "component": component,
            "message": message,
            "metadata": metadata,
            "created_at": timestamp.isoformat()
        }

        # Save to database
        try:
            async with AsyncSessionLocal() as session:
                log_entry = ActivityLog(
                    level=level,
                    component=component,
                    message=message,
                    metadata_json=metadata,
                    created_at=timestamp
                )
                session.add(log_entry)
                await session.commit()
                payload["id"] = log_entry.id
        except Exception as e:
            print(f"[ActivityService] Error persisting log: {e}")

        # Broadcast to SSE subscribers
        for queue in list(self._subscribers):
            try:
                await queue.put(payload)
            except Exception:
                pass

activity_service = ActivityService()
