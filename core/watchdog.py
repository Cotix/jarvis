import asyncio
import logging
import os
from datetime import datetime
from typing import List, Dict

from core.script import Script
from core.service import Service, Status
from core.state import State
from settings import Settings


class Watchdog:
    _logger = logging.getLogger('Watchdog')
    _settings = Settings()
    _state: State
    _scripts: Dict[str, Script]

    def __init__(self, state: State):
        self._state = state
        self._scripts = dict

    async def _check_service(self, service: Service):
        if service.heartbeat_required and service.last_status != Status.DOWN:
            delta = (datetime.now() - service.last_heartbeat).total_seconds()
            if delta > self._settings.heartbeat_timeout:
                await self._state.update_service(service.name, Status.DOWN, False)

    async def _load_scripts(self):
        for root, dirs, files in os.walk(self._settings.scripts_path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and os.access(file_path, os.X_OK) and file not in self._scripts:
                    self._logger.info(f'Found script: {file}')
                    self._scripts[file] = Script(file, self._state)
                    await self._scripts[file].load()

        self._scripts = {k: v for k, v in self._scripts.items() if os.path.exists(f'{self._settings.scripts_path}{k}')}

    async def run(self):
        self._logger.info(f'Starting watchdog')
        while True:
            await self._load_scripts()
            for service in self._state.all_services():
                await self._check_service(service)
            await asyncio.gather(*[script.push_events() for script in self._scripts])
            if (datetime.now() - self._state.last_save).total_seconds() >= 60:
                self._state.save()
            await asyncio.sleep(1)

