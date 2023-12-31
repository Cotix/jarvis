import logging

from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from settings import Settings


class Slack:
    _logger = logging.getLogger('Slack')
    _settings = Settings()

    def __init__(self):
        self._username = "Jarvis"
        self._client = AsyncWebClient(token=self._settings.slack_key)

    async def post_message(self, channel, message):
        try:
            await self._client.chat_postMessage(channel=channel.lower(), text=message)
        except SlackApiError as e:
            self._logger.exception('Could not post slack')
