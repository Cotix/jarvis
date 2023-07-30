from typing import Dict

from core.consumer import Consumer
from core.service import Service, Status
from slack.slack import Slack


class SlackStatusConsumer(Consumer):
    _channels: Dict[str, str]
    _slack: Slack

    def __init__(self, slack: Slack, channels: Dict[str, str]):
        self._channels = channels
        self._slack = slack

    async def consume(self, current: Service, last: Service):
        channel = self._channels.get(current.name, current.name)
        if current.last_status != last.last_status:
            msg = self._format_status_msg(current, last)
            if channel:
                await self._slack.post_message(channel, msg)
            await self._slack.post_message('jarvis', msg)

        if current.event:
            msg = self._format_event_msg(current)
            await self._slack.post_message(channel, msg)

    def _format_status_msg(self, current: Service, last: Service) -> str:
        return f'[{current.last_status}] {current.name} went from {last.last_status} to {current.last_status} at {current.last_check}!'

    def _format_event_msg(self, current: Service) -> str:
        return f'[EVENT][{current.event.type}] {", ".join([f"{k}: {v}" for k, v in current.event.fields.items()])}'
