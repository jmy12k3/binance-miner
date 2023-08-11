import logging.handlers
from typing import Optional, Union

from .notifications import NotificationHandler


class Logger:
    Logger = None
    NotificationHandler = None

    def __init__(
        self, logging_service: Union[str, None], enable_notifications: Optional[bool] = False
    ):
        self.Logger = logging.getLogger(f"{logging_service}_logger")
        self.Logger.setLevel(logging.DEBUG)
        self.Logger.propagate = False
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        if logging_service:
            fh = logging.FileHandler(f"logs/{logging_service}.log")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            self.Logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.Logger.addHandler(ch)
        self.NotificationHandler = NotificationHandler(enable_notifications)

    def close(self):
        for handler in self.Logger.handlers[:]:
            handler.close()

    def log(self, message: str, level: int, notification: Optional[bool] = True):
        # Mypy references
        assert self.Logger and self.NotificationHandler

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

    def debug(self, message: str, notification: Optional[bool] = False):
        self.log(message, logging.DEBUG, notification)

    def info(self, message: str, notification: Optional[bool] = True):
        self.log(message, logging.INFO, notification)

    def warning(self, message: str, notification: Optional[bool] = True):
        self.log(message, logging.WARNING, notification)

    def error(self, message: str, notification: Optional[bool] = True):
        self.log(message, logging.ERROR, notification)
