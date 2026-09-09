import asyncio
import json
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from app.services.activity_service import activity_service

router = APIRouter(prefix="/stream", tags=["Stream"])

@router.get("/activity")
async def stream_activity(request: Request):
    queue = activity_service.subscribe()

    async def event_generator():
        try:
            # Yield initial connection message
            yield {
                "event": "connected",
                "data": json.dumps({"status": "connected", "message": "Real-time activity stream connected."})
            }

            while True:
                if await request.is_disconnected():
                    break

                try:
                    # Wait for new log events with a 15-second heartbeat timeout
                    log_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "event": "activity",
                        "data": json.dumps(log_data)
                    }
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield {
                        "event": "ping",
                        "data": json.dumps({"ping": True})
                    }
        finally:
            activity_service.unsubscribe(queue)

    return EventSourceResponse(event_generator())
