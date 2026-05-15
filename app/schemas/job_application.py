from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.job_application import JobApplicationStatus, JobPlatform


class JobApplicationBase(BaseModel):
    job_title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    url: str = Field(min_length=1, max_length=500)
    status: JobApplicationStatus = JobApplicationStatus.APPLIED
    notes: str | None = None
    platform: JobPlatform = JobPlatform.LINKEDIN


class JobApplicationCreate(JobApplicationBase):
    pass


class JobApplicationUpdate(BaseModel):
    status: JobApplicationStatus | None = None
    notes: str | None = None


class JobApplicationRead(JobApplicationBase):
    id: int
    applied_at: datetime
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)
