import json
import logging
from threading import Thread
from typing import Dict, List

import websockets.sync.server
from websockets.sync.server import ServerConnection

from core.consumer import Consumer
from core.service import Service
from settings import Settings


class WarroomConsumer(Consumer):
    _logger = logging.getLogger('Warroom')
    _clients: List[ServerConnection]

    def __init__(self):
        self._clients = []
        Thread(target=self._serve).start()

    def _serve(self):
        self._logger.info(f'Starting warroom server')
        with websockets.sync.server.serve(self.handler, host=Settings.warroom_host, port=Settings.warroom_port) as server:
            server.serve_forever()

    def handler(self, socket: ServerConnection):
        self._clients.append(socket)
        try:
            for msg in socket:
                pass
        except:
            pass
        self._clients = [x for x in self._clients if x != socket]

    async def consume(self, current: Service, last: Service):
        pass

    async def end_of_day(self, pnls: Dict[str, float]):
        pass

    async def pnl_update(self, name: str, pnl: float):
        msg = json.dumps({'service': name, 'pnl': pnl})
        to_remove = []
        for client in self._clients:
            try:
                client.send(msg)
            except:
                to_remove.append(client)
        self._clients = [x for x in self._clients if x not in to_remove]
