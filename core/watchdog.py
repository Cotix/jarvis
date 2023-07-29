import asyncio
import logging
from datetime import datetime

from core.service import Service, Status
from core.state import State
from settings import Settings


class Watchdog:
    _logger = logging.getLogger('Watchdog')
    _settings = Settings()
    _state: State

    def __init__(self, state: State):
        self._state = state

    async def _check_service(self, service: Service):
        if service.heartbeat_required and service.last_status != Status.DOWN:
            delta = (datetime.now() - service.last_heartbeat).total_seconds()
            if delta > self._settings.heartbeat_timeout:
                await self._state.update_service(service.name, Status.DOWN, False)

    async def run(self):
        self._logger.info(f'Starting watchdog')
        while True:
            for service in self._state.all_services():
                await self._check_service(service)
            if (datetime.now() - self._state.last_save).total_seconds() >= 60:
                self._state.save()
            await asyncio.sleep(1)

