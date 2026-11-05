"""WebSocket stream of live gauge fabric (NAVD88 WSE)."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("PTDT.WS.Hydrology")
router = APIRouter()

_clients: Set[WebSocket] = set()
_poll_task: asyncio.Task | None = None
POLL_SECONDS = 30


async def _broadcast(payload: dict) -> None:
    dead = []
    text = json.dumps(payload)
    for ws in list(_clients):
        try:
            await ws.send_text(text)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _clients.discard(ws)


async def _poll_loop() -> None:
    from backend.core.data_fabric import TriStateDataFabric

    fabric = TriStateDataFabric()
    while True:
        try:
            obs = await fabric.get_live_hydrologic_fabric()
            await _broadcast(
                {
                    "type": "gauge_fabric",
                    "count": len(obs),
                    "observations": [o.model_dump() for o in obs],
                }
            )
        except Exception as exc:
            logger.warning("poll error: %s", exc)
            await _broadcast({"type": "error", "detail": str(exc)})
        await asyncio.sleep(POLL_SECONDS)


def ensure_poller() -> None:
    global _poll_task
    if _poll_task is None or _poll_task.done():
        _poll_task = asyncio.create_task(_poll_loop())


@router.websocket("/ws/hydrology")
async def ws_hydrology(websocket: WebSocket) -> None:
    await websocket.accept()
    _clients.add(websocket)
    ensure_poller()
    try:
        await websocket.send_text(json.dumps({"type": "hello", "poll_s": POLL_SECONDS}))
        while True:
            # keep-alive / client pings
            msg = await websocket.receive_text()
            if msg.strip().lower() in ("ping", "{\"type\":\"ping\"}"):
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    finally:
        _clients.discard(websocket)
