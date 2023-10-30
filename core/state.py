import asyncio
import logging
import os.path
import pickle
from datetime import datetime
from typing import List, Dict, Optional

from core.consumer import Consumer
from core.service import Service, Status, Event


class State:
    _logger = logging.getLogger('State')
    _services: Dict[str, Service]
    _consumers: List[Consumer]
    _last_save: datetime
    _trades: List[Event]

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
            self._trades = data.get('trades', [])
            self._logger.info('Loaded state')

    def save(self):
        data = {'services': self._services, 'last_save': datetime.now(), 'trades': self._trades}
        with open('state.dat', 'wb') as f:
            pickle.dump(data, f)
        self._logger.info('Saved state')
        self._last_save = data['last_save']

    async def end_of_day(self):
        if not self._trades:
            return
        with open('trades.csv', 'a') as f:
            f.write('\n'.join([f'{t.timestamp.timestamp()},{t.source},{t.fields.get("pnl", 0)}' for t in self._trades]))
            f.write('\n')

        sources = set([t.source.lower() for t in self._trades])
        pnls = {}
        for source in sources:
            pnls[source] = sum(t.fields.get('pnl', 0) for t in self._trades if t.source.lower() == source)
        with open('eod.csv', 'a') as f:
            f.write(f'{datetime.now()},{pnls}\n')
        self._trades = []
        await asyncio.gather(*[consumer.end_of_day(pnls) for consumer in self._consumers])


    def add_consumer(self, consumer: Consumer):
        self._logger.info(f'Registering {type(consumer)} as a consumer!')
        self._consumers.append(consumer)

    async def register_service(self, name: str, heartbeat_required: bool):
        if name in self._services:
            raise Exception('Service name already registered!')
        self._services[name] = Service(name, datetime.fromtimestamp(0), Status.UNKNOWN, heartbeat_required, datetime.fromtimestamp(0), None)
        self._logger.info(f'Registered service {name}')
        self.save()

    async def update_service(self, name: str, status: Status, heartbeat: bool):
        if name not in self._services:
            raise Exception('Unknown service name!')
        last = self._services[name]
        self._services[name] = Service(name, datetime.now(), status, last.heartbeat_required, datetime.now() if heartbeat else last.last_heartbeat, None)
        self._logger.debug(f'Updating service from {last} to {self._services[name]}')
        await asyncio.gather(*[consumer.consume(self._services[name], last) for consumer in self._consumers])

    async def publish_event(self, name: str, event: Event):
        if name not in self._services:
            raise Exception('Unknown service name!')
        if event.type == 'TRADE':
            self._trades.append(event)
        last = self._services[name]
        self._services[name] = Service(name, datetime.now(), last.last_status, last.heartbeat_required, last.last_heartbeat, event)
        self._logger.debug(f'Updating service from {last} to {self._services[name]}')
        await asyncio.gather(*[consumer.consume(self._services[name], last) for consumer in self._consumers])

    def get_service(self, name: str) -> Optional[Service]:
        return self._services.get(name)

    def all_services(self) -> List[Service]:
        return list(self._services.values())

    @property
    def last_save(self) -> datetime:
        return self._last_save
