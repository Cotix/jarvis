import asyncio
import threading
from asyncio import AbstractEventLoop
from datetime import datetime
import logging
from typing import Dict, Union

import uvicorn
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from uvicorn import Config, Server

from core.service import Event, Status
from core.state import State


class HttpEvent(BaseModel):
    timestamp: float
    source: str
    type: str
    service: str
    fields: Dict[str, Union[str, int, bool]]


class HttpRegister(BaseModel):
    service: str
    heartbeat: bool


class HTTPEndpoint:
    _logger = logging.getLogger('HTTPEndpoint')
    _state: State
    _app: FastAPI
    _router: APIRouter

    def __init__(self, state: State, main_loop: AbstractEventLoop):
        self._state = state
        self._app = FastAPI()
        self._router = APIRouter()
        self._main_loop = main_loop

    async def _register_endpoints(self):
        self._router.add_api_route("/publish/event", endpoint=self._publish_event, methods=["POST"])
        self._router.add_api_route("/publish/heartbeat/{service_name}", endpoint=self._publish_heartbeat, methods=["POST"])
        self._router.add_api_route("/register", endpoint=self._register_service, methods=["POST"])
        self._app.include_router(self._router)

    async def _publish_event(self, http_event: HttpEvent):
        event = Event(
            timestamp=datetime.fromtimestamp(http_event.timestamp),
            source=http_event.source,
            type=http_event.type,
            fields=http_event.fields
        )
        self._main_loop.create_task(self._state.publish_event(http_event.service, event))

    async def _publish_heartbeat(self, service_name: str):
        self._main_loop.create_task(self._state.update_service(service_name, Status.OK, True))

    async def _register_service(self, data: HttpRegister):
        self._main_loop.create_task(self._state.register_service(data.service, data.heartbeat))

    async def run(self):
        await self._register_endpoints()
        config = Config(app=self._app, loop="asyncio")
        server = Server(config)
        await server.serve()
        raise Exception("Uvicorn exited")
