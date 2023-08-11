import logging.handlers

from .notifications import NotificationHandler


class Logger:
    Logger = None
    NotificationHandler = None

    def __init__(self, logging_service: str = "crypto_trading", enable_notifications: bool = True):
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

    def log(self, message, level: str = "info", notification: bool = True):
        if level == "info":
            self.Logger.info(message)
        elif level == "warning":
            self.Logger.warning(message)
        elif level == "error":
            self.Logger.error(message)
        elif level == "debug":
            self.Logger.debug(message)

        if notification and self.NotificationHandler.enabled:
            self.NotificationHandler.send_notification(str(message))

    def info(self, message, notification: bool = True):
        self.log(message, "info", notification)

    def warning(self, message, notification: bool = True):
        self.log(message, "warning", notification)

    def error(self, message, notification: bool = True):
        self.log(message, "error", notification)

    def debug(self, message, notification: bool = False):
        self.log(message, "debug", notification)
