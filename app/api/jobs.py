from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.job_application import JobApplication, JobApplicationStatus
from app.schemas.job_application import (
    JobApplicationCreate,
    JobApplicationRead,
    JobApplicationUpdate,
)
from app.security import require_api_key

router = APIRouter(prefix="/jobs", tags=["jobs"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[JobApplicationRead])
def list_jobs(
    status_filter: JobApplicationStatus | None = Query(default=None, alias="status"),
    company: str | None = None,
    db: Session = Depends(get_db),
) -> list[JobApplication]:
    query = select(JobApplication).order_by(JobApplication.applied_at.desc())
    if status_filter:
        query = query.where(JobApplication.status == status_filter)
    if company:
        query = query.where(JobApplication.company.ilike(f"%{company}%"))
    return list(db.scalars(query))


@router.post("", response_model=JobApplicationRead, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobApplicationCreate, db: Session = Depends(get_db)) -> JobApplication:
    job = JobApplication(**payload.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.patch("/{job_id}", response_model=JobApplicationRead)
def update_job(
    job_id: int,
    payload: JobApplicationUpdate,
    db: Session = Depends(get_db),
) -> JobApplication:
    job = db.get(JobApplication, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, key, value)

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_db)) -> None:
    job = db.get(JobApplication, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    db.delete(job)
    db.commit()
