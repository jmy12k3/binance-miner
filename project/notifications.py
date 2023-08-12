import queue
from os import path
from threading import Thread

import apprise

from .config import CONFIG_PATH


class NotificationHandler:
    APPRISE_CONFIG_PATH = path.join(CONFIG_PATH, "apprise.yml")

    def __init__(self, enabled: bool | None = True):
        if enabled and path.exists(self.APPRISE_CONFIG_PATH):
            self.apobj = apprise.Apprise()
            config = apprise.AppriseConfig()
            config.add(self.APPRISE_CONFIG_PATH)
            self.apobj.add(config)
            self.queue = queue.Queue()  # type: ignore
            self.start_worker()
            self.enabled = True
        else:
            self.enabled = False

    def start_worker(self):
        Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        while True:
            message, attachments = self.queue.get()
            if attachments:
                self.apobj.notify(body=message, attach=attachments)
            else:
                self.apobj.notify(body=message)
            self.queue.task_done()

    def send_notification(self, message, attachments=None):
        if self.enabled:
            self.queue.put((message, attachments or []))
