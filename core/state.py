import asyncio
import logging
import os.path
import pickle
import json

from datetime import datetime
from typing import List, Dict, Optional

from core.consumer import Consumer
from core.service import Service, Status, Event, EndOfDay


class State:
    _logger = logging.getLogger('State')
    _services: Dict[str, Service]
    _consumers: List[Consumer]
    _last_save: datetime
    _trades: List[Event]
    _values: Dict[str, Event]
    _pnl: Dict[str, float]

    def __init__(self):
        self._services = {}
        self._consumers = []
        self._pnl = {}
        self._last_save = datetime.fromtimestamp(0)

    def load(self):
        if os.path.exists('state.dat'):
            with open('state.dat', 'rb') as f:
                data = pickle.load(f)
            self._services.update(data.get('services', {}))
            self._last_save = data.get('last_save', datetime.now())
            self._trades = data.get('trades', [])
            if isinstance(data.get('values', []), list):
                self._values = {x.source: x for x in data.get('values', [])}
            else:
                self._values = data.get('values')

            sources = set([t.source.lower() for t in self._trades])
            self._pnl = {}
            for source in sources:
                self._pnl[source] = sum(float(t.fields.get('pnl', 0)) for t in self._trades if t.source.lower() == source)
            self._logger.info('Loaded state')

    def save(self):
        data = {'services': self._services, 'last_save': datetime.now(), 'trades': self._trades, 'values': self._values}
        with open('state.dat', 'wb') as f:
            pickle.dump(data, f)
        self._logger.info('Saved state')
        self._last_save = data['last_save']

    async def end_of_day(self):
        if not self._trades and not self._values:
            return
        with open('trades.csv', 'a') as f:
            f.write('\n'.join([f'{t.timestamp.timestamp()},{t.source},{t.fields.get("pnl", 0)},{t.fields.get("volume", 0)},{json.dumps(t.fields)}' for t in self._trades]))
            f.write('\n')

        end_of_days = {}

        sources = set([t.source.lower() for t in self._trades])
        pnls = {}
        for source in sources:
            pnls[source] = sum(float(t.fields.get('pnl', 0)) for t in self._trades if t.source.lower() == source)
            end_of_days[source] = EndOfDay(pnls[source], 0)
        with open('eod.csv', 'a') as f:
            f.write(f'{datetime.now().timestamp()},{pnls}\n')

        for value in self._values.values():
            end_of_days[value.source] = end_of_days.get(value.source, EndOfDay(0, 0))._replace(value=value.fields.get('value', 0))

        self._trades = []
        self._values = {}
        self._pnl = {}
        self.save()
        await asyncio.gather(*[consumer.end_of_day(end_of_days) for consumer in self._consumers])

    def add_consumer(self, consumer: Consumer):
        self._logger.info(f'Registering {type(consumer)} as a consumer!')
        self._consumers.append(consumer)

    async def register_service(self, name: str, heartbeat_required: bool):
        if name in self._services:
            self._logger.info(f'Service name {name} already registered')
            return
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
            self._pnl[event.source.lower()] = self._pnl.get(event.source.lower(), 0.0) + event.fields['pnl']
            await asyncio.gather(*[consumer.pnl_update(name, self._pnl[event.source.lower()]) for consumer in self._consumers])
        if event.type == "VALUE":
            self._values[event.source.lower()] = event
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
