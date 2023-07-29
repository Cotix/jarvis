import os

from util.singleton import Singleton


class Settings(metaclass=Singleton):
    heartbeat_timeout: int = int(os.getenv('HEARTBEAT_TIMEOUT', 60))
    telegram_key: str = os.getenv('TELEGRAM_KEY')
    slack_key: str = os.getenv('SLACK_KEY')
