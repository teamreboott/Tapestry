import logging
import structlog
import datetime
from concurrent_log_handler import ConcurrentRotatingFileHandler
from src.handler.slackbot import SlackWebhookHandler
from zoneinfo import ZoneInfo

SEOUL_TZ = ZoneInfo("Asia/Seoul")

def seoul_time_stamper(_: structlog.typing.WrappedLogger, __: str, event_dict: dict) -> dict:
    """Add ISO‑8601 timestamp in Asia/Seoul time zone (UTC+9)."""
    event_dict["timestamp"] = datetime.datetime.now(tz=SEOUL_TZ).isoformat()
    return event_dict

def configure_logging(log_file: str) -> None:
    """Configure logging with console, rotating file and Slack handlers."""

    # 1) 기본 root logger 설정 (console only for now)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler()],  # attach other handlers below
    )

    # 2) ConcurrentRotatingFileHandler (INFO 이상)
    rotating_handler = ConcurrentRotatingFileHandler(
        log_file,
        mode="a",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,  # keep last 5 log files
        encoding="utf-8",
    )
    rotating_handler.setLevel(logging.INFO)

    # 3) Slack handler (WARNING 이상)
    slack_handler = SlackWebhookHandler(level=logging.ERROR)

    # 4) Attach additional handlers to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(rotating_handler)
    root_logger.addHandler(slack_handler)

    # 5) structlog 설정 (root logger 이미 설정된 level 사용)
    structlog.configure(
        processors=[
            seoul_time_stamper,             # 아시아/서울 ISO‑8601 타임스탬프
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    for noisy in ("httpx", "httpcore", "LiteLLM"):
        logging.getLogger(noisy).setLevel(logging.ERROR)