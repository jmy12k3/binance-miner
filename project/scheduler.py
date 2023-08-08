import datetime
import logging
from traceback import format_exc

from schedule import Job, Scheduler


class SafeScheduler(Scheduler):
    def __init__(self, logger: logging.Logger, rerun_immediately=True):
        self.logger = logger
        self.rerun_immediately = rerun_immediately
        super().__init__()

    def _run_job(self, job: Job):
        try:
            super()._run_job(job)
        except Exception:  # pylint: disable=broad-except
            self.logger.error(f"Error while {next(iter(job.tags))}: {format_exc()}")
            job.last_run = datetime.datetime.now()
            if not self.rerun_immediately:
                job._schedule_next_run()  # pylint: disable=protected-access
