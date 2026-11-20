"""
AEGIS backend entrypoint.

Wires together the FastAPI app, the shared MissionEngine, REST routes,
and the WebSocket telemetry stream + background tick loop.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from api.routes import build_router
from api.security_routes import router as security_router
from api.cyberrange_routes import router as cyberrange_router
from simulation.engine import MissionEngine
from websocket.manager import run_simulation_loop, websocket_endpoint

engine = MissionEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_simulation_loop(engine))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="ARES Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(build_router(engine), prefix="/api")
app.include_router(security_router, prefix="/api")
app.include_router(cyberrange_router, prefix="/api")


@app.websocket("/ws/telemetry")
async def telemetry_ws(ws: WebSocket) -> None:
    await websocket_endpoint(ws, engine)


@app.get("/")
def root() -> dict:
    return {"name": "ARES Backend", "status": "online"}
