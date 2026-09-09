import asyncio
import logging
import os
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger("KeepAlive")

class KeepAliveService:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self.interval_seconds = 10 * 60 # 10 minutes (Render spins down after 15 min idle)

    def _get_target_url(self) -> Optional[str]:
        # Render automatically injects RENDER_EXTERNAL_URL (e.g. https://auto-apply-backend.onrender.com)
        external_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("KEEP_ALIVE_URL")
        if external_url:
            return f"{external_url.rstrip('/')}/health"
        return None

    async def _ping_loop(self):
        target_url = self._get_target_url()
        if not target_url:
            logger.info("[KeepAlive] No external URL detected (RENDER_EXTERNAL_URL or KEEP_ALIVE_URL). Running in local mode.")
            return

        logger.info(f"[KeepAlive] Anti-sleep self-pinger initialized. Target: {target_url} (Every {self.interval_seconds // 60} min)")
        
        # Initial delay before starting the ping loop
        await asyncio.sleep(60)

        async with httpx.AsyncClient(timeout=15.0) as client:
            while self._running:
                try:
                    res = await client.get(target_url)
                    if res.status_code == 200:
                        logger.info(f"[KeepAlive] Heartbeat ping successful -> {target_url} (HTTP 200)")
                    else:
                        logger.warning(f"[KeepAlive] Heartbeat ping returned HTTP {res.status_code}")
                except Exception as e:
                    logger.warning(f"[KeepAlive] Heartbeat ping failed: {e}")

                await asyncio.sleep(self.interval_seconds)

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._ping_loop())

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

keep_alive_service = KeepAliveService()
