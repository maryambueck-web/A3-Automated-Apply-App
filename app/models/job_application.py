from datetime import datetime
from enum import Enum as PythonEnum

from sqlalchemy import DateTime, Enum as SqlEnum, Integer, String, Text
from sqlalchemy.orm import mapped_column

from app.db import Base


class JobApplicationStatus(str, PythonEnum):
    APPLIED = "applied"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"


class JobPlatform(str, PythonEnum):
    LINKEDIN = "LinkedIn"


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = mapped_column(Integer, primary_key=True, index=True)
    job_title = mapped_column(String(255), nullable=False)
    company = mapped_column(String(255), nullable=False)
    url = mapped_column(String(500), nullable=False)
    status = mapped_column(
        SqlEnum(JobApplicationStatus, name="job_application_status"),
        default=JobApplicationStatus.APPLIED,
        nullable=False,
    )
    applied_at = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_updated = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    notes = mapped_column(Text, nullable=True)
    platform = mapped_column(
        SqlEnum(JobPlatform, name="job_platform"), default=JobPlatform.LINKEDIN, nullable=False
    )
