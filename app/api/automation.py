from datetime import datetime
from re import sub

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from app.automation.application_letter_template import (
    ApplicationLetterContext,
    render_application_letter,
    render_application_letter_pdf_bytes,
)
from app.automation.scheduler import get_scheduler_service
from app.security import require_api_key

router = APIRouter(prefix="/automation", tags=["automation"], dependencies=[Depends(require_api_key)])


class AutomationRunResponse(BaseModel):
    status: str
    started_at: datetime
    jobs_found: int
    jobs_applied: int
    message: str


class AutomationStatusResponse(BaseModel):
    enabled: bool
    schedule: str
    daily_limit: int
    last_run_at: datetime | None
    last_run_result: str | None
    last_jobs_found: int
    last_jobs_applied: int


class ApplicationLetterPdfRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=255)
    sender_name: str = Field(min_length=1, max_length=255)
    recipient_name: str | None = Field(default=None, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    custom_salutation: str | None = Field(default=None, max_length=255)
    file_name: str | None = Field(default=None, max_length=255)


class ApplicationLetterPreviewRequest(BaseModel):
    job_title: str | None = Field(default=None, max_length=255)
    sender_name: str | None = Field(default=None, max_length=255)
    recipient_name: str | None = Field(default=None, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    custom_salutation: str | None = Field(default=None, max_length=255)


class ApplicationLetterPreviewResponse(BaseModel):
    content: str


@router.post("/run", response_model=AutomationRunResponse)
def run_automation() -> AutomationRunResponse:
    scheduler = get_scheduler_service()
    result = scheduler.run_once()
    return AutomationRunResponse(
        status="completed",
        started_at=result.started_at,
        jobs_found=result.jobs_found,
        jobs_applied=result.jobs_applied,
        message=result.message,
    )


@router.get("/status", response_model=AutomationStatusResponse)
def automation_status() -> AutomationStatusResponse:
    scheduler = get_scheduler_service()
    return AutomationStatusResponse(
        enabled=True,
        schedule=scheduler.schedule,
        daily_limit=scheduler.daily_limit,
        last_run_at=scheduler.last_run_at,
        last_run_result=scheduler.last_run_result,
        last_jobs_found=scheduler.last_jobs_found,
        last_jobs_applied=scheduler.last_jobs_applied,
    )


@router.post("/application-letter/pdf")
def generate_application_letter_pdf(payload: ApplicationLetterPdfRequest) -> Response:
    context = _build_application_letter_context(payload)
    pdf_bytes = render_application_letter_pdf_bytes(context)
    filename = _build_pdf_filename(payload.file_name, payload.job_title)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/application-letter/preview", response_model=ApplicationLetterPreviewResponse)
def preview_application_letter(payload: ApplicationLetterPreviewRequest) -> ApplicationLetterPreviewResponse:
    context = _build_application_letter_context(payload)
    return ApplicationLetterPreviewResponse(content=render_application_letter(context))


def _build_pdf_filename(file_name: str | None, job_title: str) -> str:
    source = (file_name or f"application-letter-{job_title}").strip().lower()
    slug = sub(r"[^a-z0-9]+", "-", source).strip("-") or "application-letter"
    if not slug.endswith(".pdf"):
        slug = f"{slug}.pdf"
    return slug


def _build_application_letter_context(payload: ApplicationLetterPdfRequest | ApplicationLetterPreviewRequest) -> ApplicationLetterContext:
    return ApplicationLetterContext(
        job_title=(payload.job_title or "[Job Title]").strip(),
        sender_name=(payload.sender_name or "[Your Name]").strip(),
        recipient_name=(payload.recipient_name or None),
        company_name=(payload.company_name or None),
        custom_salutation=(payload.custom_salutation or None),
    )
