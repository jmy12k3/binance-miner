# mypy: disable-error-code=union-attr
import logging.handlers
from logging.handlers import RotatingFileHandler

from .notifications import NotificationHandler


class DummyLogger:
    Logger = None

    def __init__(self):
        self.Logger = logging.getLogger(__name__)
        self.Logger.addHandler(logging.NullHandler())
        self.Logger.propagate = False

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class Logger:
    Logger = None
    NotificationHandler = None

    def __init__(self, logging_service: str, enable_notifications: bool = False):
        self.Logger = logging.getLogger(logging_service)
        self.Logger.setLevel(logging.DEBUG)
        self.Logger.propagate = False
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Initialize file handler
        fh = RotatingFileHandler(f"logs/{logging_service}.log", maxBytes=1000000, backupCount=5)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.Logger.addHandler(fh)

        # Initialize console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.Logger.addHandler(ch)

        # Initialize notification handler
        self.NotificationHandler = NotificationHandler(enable_notifications)

    def close(self):
        for handler in self.Logger.handlers[:]:
            handler.close()

    def log(self, message: str, level: int, notification: bool):
        if level == logging.DEBUG:
            self.Logger.debug(message)
        elif level == logging.INFO:
            self.Logger.info(message)
        elif level == logging.WARNING:
            self.Logger.warning(message)
        elif level == logging.ERROR:
            self.Logger.error(message)
        if notification and self.NotificationHandler.enabled:
            self.NotificationHandler.send_notification(str(message))

    def debug(self, message: str, notification: bool = False):
        self.log(message, logging.DEBUG, notification)

    def info(self, message: str, notification: bool = True):
        self.log(message, logging.INFO, notification)

    def warning(self, message: str, notification: bool = True):
        self.log(message, logging.WARNING, notification)

    def error(self, message: str, notification: bool = True):
        self.log(message, logging.ERROR, notification)
