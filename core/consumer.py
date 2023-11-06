from abc import ABC, abstractmethod
from typing import Dict

from core.service import Service, EndOfDay


class Consumer(ABC):

    @abstractmethod
    def consume(self, current: Service, last: Service):
        pass

    @abstractmethod
    def end_of_day(self, eod: Dict[str, EndOfDay]):
        pass
