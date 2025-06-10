import asyncio
import logging
import os

import httpx


class SlackWebhookHandler(logging.Handler):
    def __init__(self, level=logging.WARNING):
        super().__init__(level)
        self.webhook_url = os.environ["SLACK_WEBHOOK_URL"]

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        try:
            httpx.post(self.webhook_url, json={"text": f"```{msg}```"}, timeout=5)
        except Exception as exc:
            logging.getLogger("SlackWebhookHandler").error("Slack send failed: %s", exc)

