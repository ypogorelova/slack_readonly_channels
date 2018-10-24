import asyncio
import os
import sys
import logging

import dotenv
from aslack.slack_bot import SlackBot
from aslack.slack_api import SlackApiError

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

LOG_FILENAME = 'logfile'

logger = logging.getLogger(__name__)


class BlockBot(SlackBot):
        """Slack block bot deletes messages from certain users.

        :param id_: the bot's slack id
        :param user: the bot's friendly name
        :param api: the slack api wrapper.
        """

        def __init__(self, id_, user, api):
            super().__init__(id_, user, api)
            self.channel = os.environ["CHANNEL"]

        async def handle_message(self, message, filters):
            """Handle an incoming message appropriately.
            :param message: the incoming message to handle
            :param filters: the filters to apply to incoming messages.
            """

            data = self._unpack_message(message)
            logger.debug("Incoming message: %s", data)
            if data.get('type') == 'error':
                raise SlackApiError(
                    data.get('error', {}).get('msg', str(data))
                )
            if data.get('type') == 'message' and data.get('channel') == self.channel:
                user = data.get('user')
                if user and user in os.environ["RESTRICTED_USERS"]:
                    ts = data.get('ts')
                    logger.debug("TS of message to delete: %s", ts)
                    try:
                        await self.api.execute_method('chat.delete', channel=self.channel, ts=ts)
                    #  actually this will not help because SlackBot closes socket on error
                    except SlackApiError as e:
                        logger.error(e)
                        raise


if __name__ == '__main__':
    try:
        slack_token = os.environ["SLACK_API_TOKEN"]
    except KeyError as error:
        sys.stderr.write('Please set the environment variable {0}'.format(error))
        sys.exit(1)

    logging.basicConfig(
        datefmt='%Y/%m/%d %H.%M.%S',
        format='%(levelname)s:%(name)s:%(message)s',
        level=logging.DEBUG,
        stream=sys.stdout,
    )

    LOOP = asyncio.get_event_loop()
    BOT = LOOP.run_until_complete(BlockBot.from_api_token())
    LOOP.run_until_complete(BOT.join_rtm())
    LOOP.close()
