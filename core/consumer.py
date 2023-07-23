from abc import ABC, abstractmethod

from core.service import Service


class Consumer(ABC):

    @abstractmethod
    def consume(self, current: Service, last: Service):
        pass