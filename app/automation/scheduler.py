from datetime import datetime

from app.automation.linkedin_bot import AutomationResult, LinkedInBot
from app.config import get_settings


class SchedulerService:
    def __init__(self) -> None:
        settings = get_settings()
        self.schedule = settings.linkedin_schedule_cron
        self.daily_limit = settings.linkedin_daily_limit
        self.last_run_at: datetime | None = None
        self.last_run_result: str | None = None
        self.last_jobs_found: int = 0
        self.last_jobs_applied: int = 0

    def run_once(self) -> AutomationResult:
        result = LinkedInBot().run()
        self.last_run_at = result.started_at
        self.last_run_result = result.message
        self.last_jobs_found = result.jobs_found
        self.last_jobs_applied = result.jobs_applied
        return result


scheduler_service = SchedulerService()


def get_scheduler_service() -> SchedulerService:
    return scheduler_service
