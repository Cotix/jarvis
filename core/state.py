import asyncio
import logging
import os.path
import pickle
from datetime import datetime
from typing import List, Dict, Optional

from core.consumer import Consumer
from core.service import Service, Status


class State:
    _logger = logging.getLogger('State')
    _services: Dict[str, Service]
    _consumers: List[Consumer]
    _last_save: datetime

    def __init__(self):
        self._services = {}
        self._consumers = []
        self._last_save = datetime.fromtimestamp(0)

    def load(self):
        if os.path.exists('state.dat'):
            with open('state.dat', 'rb') as f:
                data = pickle.load(f)
            self._services.update(data.get('services', {}))
            self._last_save = data.get('last_save', datetime.now())
            self._logger.info('Loaded state')

    def save(self):
        data = {'services': self._services, 'last_save': datetime.now()}
        with open('state.dat', 'wb') as f:
            pickle.dump(data, f)
        self._logger.info('Saved state')

    def register_service(self, name: str, heartbeat_required: bool):
        if name in self._services:
            raise Exception('Service name already registered!')
        self._services[name] = Service(name, datetime.fromtimestamp(0), Status.UNKNOWN, heartbeat_required, datetime.fromtimestamp(0))
        self._logger.info(f'Registered service {name}')
        self.save()

    async def update_service(self, name: str, status: Status, heartbeat: bool):
        if name not in self._services:
            raise Exception('Unknown service name!')
        last = self._services[name]
        self._services[name] = Service(name, datetime.now(), status, last.heartbeat_required, datetime.now() if heartbeat else last.last_heartbeat)
        self._logger.debug(f'Updating service from {last} to {self._services[name]}')
        await asyncio.gather(*[consumer.consume(self._services[name], last) for consumer in self._consumers])

    def get_service(self, name: str) -> Optional[Service]:
        return self._services.get(name)

    def all_services(self) -> List[Service]:
        return list(self._services.values())

    @property
    def last_save(self) -> datetime:
        return self._last_save
