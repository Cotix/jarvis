import os

from util.singleton import Singleton


class Settings(metaclass=Singleton):
    heartbeat_timeout: int = int(os.getenv('HEARTBEAT_TIMEOUT', 60))
    telegram_key: str = os.getenv('TELEGRAM_KEY')
    slack_key: str = os.getenv('SLACK_KEY')
    scripts_path: str = os.getenv('SCRIPTS_PATH', '/etc/jarvis/scripts/')
    warroom_host: str = os.getenv('WARROOM_HOST', '10.8.0.1')
    warroom_port: int = int(os.getenv('WARROOM_PORT', 8003))