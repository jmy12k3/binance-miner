import logging
import traceback
from datetime import datetime

from schedule import Job, Scheduler


# https://gist.github.com/mplewis/8483f1c24f2d6259aef6?permalink_comment_id=3703372#gistcomment-3703372
class SafeScheduler(Scheduler):
    def __init__(self, logger: logging.Logger, rerun_immediately: bool = True):
        super().__init__()
        self.logger = logger
        self.rerun_immediately = rerun_immediately

    def _run_job(self, job: Job):
        try:
            super()._run_job(job)
        except Exception:
            self.logger.error(f"\n\n{traceback.format_exc()}\n")
            job.last_run = datetime.now()
            if not self.rerun_immediately:
                job._schedule_next_run()
