import asyncio
import sys
import signal

from config import init_logging
from core.endpoints.http_endpoint import HTTPEndpoint
from core.state import State
from core.watchdog import Watchdog
from slack.consumer import SlackStatusConsumer
from slack.slack import Slack


init_logging()
state = State()
state.load()
loop = asyncio.get_event_loop()
watchdog = Watchdog(state)
http = HTTPEndpoint(state, loop)

slack = SlackStatusConsumer(Slack(), {'liquidator': 'liquidator'})
state.add_consumer(slack)

jobs = [watchdog.run(), http.run()]
loop.run_until_complete(asyncio.gather(*jobs))
