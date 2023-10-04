import json
import logging
import subprocess
import asyncio
from datetime import timedelta, datetime
from typing import List

from core.service import Event
from core.state import State
from settings import Settings


class Script:
    _logger = logging.getLogger('Script')
    _settings = Settings()
    _executable_path: str
    _interval: timedelta
    _last_run: datetime
    _state: State
    _service: str

    def __init__(self, executable: str, state: State):
        self._logger.info(f'Loading {executable} script')
        self._executable_path = f'{self._settings.scripts_path}{executable}'
        self._last_run = datetime.fromtimestamp(0)
        self._state = state

    async def load(self):
        data = await self._execute('info')
        self._interval = timedelta(seconds=data['interval'])
        self._service = data['service']

    async def _execute(self, *arguments: str) -> dict:
        process = await asyncio.create_subprocess_exec(self._executable_path, *arguments, stdout=subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=15)
        self._logger.info(f'Script {self._executable_path} returned: {stdout}')
        return json.loads(stdout)

    async def push_events(self):
        if datetime.now() - self._last_run < self._interval:
            return
        try:
            data = await self._execute('check')
        except TimeoutError:
            self._logger.warning(f'Script {self._executable_path} timed out!')
            return
        except Exception as e:
            self._logger.exception(f'Exception occured duing {self._executable_path}, possibly wrongly formatted output')

        self._last_run = datetime.now()
        events = [Event(datetime.now(), f'Script {self._executable_path.split("/")[-1]}', data['type'], data['fields']) for x in data['events']]
        for event in events:
            await self._state.publish_event(self._service, event)
