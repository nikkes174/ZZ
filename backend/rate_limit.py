from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._windows: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._last_cleanup = 0.0

    async def check(self, *, key: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        async with self._lock:
            if now - self._last_cleanup > 60:
                self._cleanup(now=now)
                self._last_cleanup = now
            self._windows[key] = max(window_seconds, self._windows.get(key, 0))
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= limit:
                retry_after = max(1, int(window_seconds - (now - hits[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests.",
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)

    def _cleanup(self, *, now: float) -> None:
        empty_keys = []
        for key, hits in self._hits.items():
            cutoff = now - self._windows.get(key, 0)
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if not hits:
                empty_keys.append(key)
        for key in empty_keys:
            self._hits.pop(key, None)
            self._windows.pop(key, None)


rate_limiter = InMemoryRateLimiter()


def client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"
    if request.client:
        return request.client.host
    return "unknown"
