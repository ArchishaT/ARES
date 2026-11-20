"""
WebSocket connection manager.

Handles the lifecycle of connected clients and broadcasts telemetry
frames produced by the shared MissionEngine tick loop. Kept separate from
`main.py` so connection bookkeeping doesn't get tangled with route
definitions.
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Set

from fastapi import WebSocket, WebSocketDisconnect

from simulation.engine import MissionEngine, TICK_DT


class ConnectionManager:
    def __init__(self) -> None:
        self.active: Set[WebSocket] = set()
        self.last_broadcast_latency_ms: float = 0.0

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def broadcast(self, payload: dict) -> None:
        if not self.active:
            return
        t0 = time.perf_counter()
        message = json.dumps(payload)
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)
        self.last_broadcast_latency_ms = (time.perf_counter() - t0) * 1000.0


manager = ConnectionManager()


async def run_simulation_loop(engine: MissionEngine) -> None:
    """Fixed-tick background loop: advances the simulation and streams a
    telemetry frame to every connected client."""
    while True:
        loop_start = time.perf_counter()
        engine.tick()

        frame = {
            "type": "telemetry",
            "sim_time_s": round(engine.sim_time_s, 2),
            "telemetry": engine.telemetry(),
            "sensors": engine.sensor_frame(),
            "logs": engine.recent_logs(limit=5),
        }
        await manager.broadcast(frame)

        elapsed = time.perf_counter() - loop_start
        await asyncio.sleep(max(0.0, TICK_DT - elapsed))


async def websocket_endpoint(ws: WebSocket, engine: MissionEngine) -> None:
    await manager.connect(ws)
    try:
        # Send an initial snapshot immediately on connect.
        await ws.send_text(json.dumps({
            "type": "init",
            "telemetry": engine.telemetry(),
            "logs": engine.recent_logs(limit=50),
        }))
        while True:
            # We don't currently expect inbound WS messages (control goes
            # over REST), but we read to detect disconnects promptly.
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)
