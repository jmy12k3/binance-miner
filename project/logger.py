import logging.handlers

from .notifications import NotificationHandler


class Logger:
    Logger = None
    NotificationHandler = None

    def __init__(self, logging_service: str | None = None, enable_notifications: bool = False):
        # Instantiate logger
        self.Logger = logging.getLogger(f"{logging_service}_logger")
        self.Logger.setLevel(logging.DEBUG)
        self.Logger.propagate = False
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Initialize notification handler
        self.NotificationHandler = NotificationHandler(enable_notifications)

        # Return for only instantiating
        if not logging_service:
            return

        # Initialize file handler
        fh = logging.FileHandler(f"logs/{logging_service}.log")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.Logger.addHandler(fh)

        # Initialize console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.Logger.addHandler(ch)

    def close(self):
        for handler in self.Logger.handlers[:]:
            handler.close()

    def log(self, message: str, level: int, notification: bool = True):
        # Ensure logger and notification handler are instantiated
        assert self.Logger and self.NotificationHandler

        # Log message
        if level == logging.DEBUG:
            self.Logger.debug(message)
        elif level == logging.INFO:
            self.Logger.info(message)
        elif level == logging.WARNING:
            self.Logger.warning(message)
        elif level == logging.ERROR:
            self.Logger.error(message)

        # Send notification
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
