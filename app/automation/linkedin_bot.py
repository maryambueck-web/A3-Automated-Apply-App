from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote_plus

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright
from sqlalchemy import func, select

from app.automation.secrets import SecretResolutionError, SecretResolver
from app.config import get_settings
from app.db import SessionLocal
from app.models.job_application import JobApplication, JobApplicationStatus, JobPlatform


@dataclass
class AutomationResult:
    started_at: datetime
    jobs_found: int
    jobs_applied: int
    message: str


@dataclass
class JobListing:
    title: str
    company: str
    url: str


class LinkedInBot:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.secret_resolver = SecretResolver()

    def run(self) -> AutomationResult:
        started_at = datetime.now(timezone.utc)
        try:
            email, password = self.secret_resolver.get_linkedin_credentials()
        except SecretResolutionError as error:
            return AutomationResult(
                started_at=started_at,
                jobs_found=0,
                jobs_applied=0,
                message=str(error),
            )

        jobs_found = 0
        jobs_applied = 0
        summaries: list[str] = []

        with SessionLocal() as db:
            applied_today = self._count_applied_today(db)
            remaining_capacity = max(self.settings.linkedin_daily_limit - applied_today, 0)
            if remaining_capacity == 0:
                return AutomationResult(
                    started_at=started_at,
                    jobs_found=0,
                    jobs_applied=0,
                    message="Daily application limit reached",
                )

            max_to_apply = min(self.settings.linkedin_max_jobs_per_run, remaining_capacity)

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.settings.linkedin_headless)
                page = browser.new_page()
                try:
                    self._login(page, email, password)
                    listings = self._search_jobs(page)
                    jobs_found = len(listings)

                    for listing in listings:
                        if jobs_applied >= max_to_apply:
                            summaries.append("Stopped after reaching the per-run or daily cap")
                            break

                        applied, note = self._apply_to_listing(page, listing)
                        self._record_application(db, listing, applied, note)
                        db.commit()
                        if applied:
                            jobs_applied += 1
                        summaries.append(f"{listing.company}: {note}")
                finally:
                    browser.close()

        return AutomationResult(
            started_at=started_at,
            jobs_found=jobs_found,
            jobs_applied=jobs_applied,
            message="; ".join(summaries[:5]) if summaries else "Automation run completed with no matching jobs",
        )

    def _count_applied_today(self, db) -> int:
        today = datetime.now(timezone.utc).date()
        statement = select(func.count()).select_from(JobApplication).where(
            JobApplication.platform == JobPlatform.LINKEDIN,
            JobApplication.status == JobApplicationStatus.APPLIED,
            func.date(JobApplication.applied_at) == today,
        )
        return int(db.scalar(statement) or 0)

    def _login(self, page: Page, email: str, password: str) -> None:
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        page.locator("#username").fill(email)
        page.locator("#password").fill(password)
        page.locator("button[type='submit']").click()
        page.wait_for_load_state("networkidle")

        if "feed" not in page.url and "checkpoint" in page.url:
            raise RuntimeError("LinkedIn requested additional verification during login")

    def _search_jobs(self, page: Page) -> list[JobListing]:
        listings: list[JobListing] = []
        for keyword in self.settings.linkedin_keyword_list:
            jobs_url = self._build_jobs_search_url(keyword)
            page.goto(jobs_url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
            cards = page.locator("div.job-card-container").all()[: self.settings.linkedin_max_jobs_per_run]
            for card in cards:
                title = card.locator("strong").first.text_content() or keyword
                company = card.locator(".artdeco-entity-lockup__subtitle").first.text_content() or "Unknown"
                link_locator = card.locator("a.job-card-container__link").first
                href = link_locator.get_attribute("href") if link_locator.count() else None
                if not href:
                    continue
                listings.append(
                    JobListing(
                        title=title.strip(),
                        company=company.strip(),
                        url=self._absolute_link(href),
                    )
                )
        deduplicated: dict[str, JobListing] = {listing.url: listing for listing in listings}
        return list(deduplicated.values())[: self.settings.linkedin_max_jobs_per_run]

    def _build_jobs_search_url(self, keyword: str) -> str:
        params = [
            f"keywords={quote_plus(keyword)}",
            f"location={quote_plus(self.settings.linkedin_default_location)}",
        ]
        if self.settings.linkedin_easy_apply_only:
            params.append("f_AL=true")
        return f"https://www.linkedin.com/jobs/search/?{'&'.join(params)}"

    def _apply_to_listing(self, page: Page, listing: JobListing) -> tuple[bool, str]:
        try:
            page.goto(listing.url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
        except PlaywrightTimeoutError:
            return False, "navigation timed out"

        easy_apply_button = page.locator("button.jobs-apply-button").first
        if easy_apply_button.count() == 0:
            return False, "Easy Apply not available"

        easy_apply_button.click()
        page.wait_for_timeout(1000)

        try:
            self._submit_easy_apply_modal(page)
            return True, "application submitted"
        except RuntimeError as error:
            self._dismiss_modal(page)
            return False, str(error)

    def _submit_easy_apply_modal(self, page: Page) -> None:
        for _ in range(8):
            submit_button = page.locator("button[aria-label='Submit application']").first
            if submit_button.count() > 0 and submit_button.is_enabled():
                submit_button.click()
                page.wait_for_timeout(1500)
                self._dismiss_modal(page)
                return

            next_button = page.locator("button[aria-label='Continue to next step'], button[aria-label='Review your application']").first
            if next_button.count() > 0 and next_button.is_enabled():
                next_button.click()
                page.wait_for_timeout(800)
                continue

            if page.locator("input[required], select[required], textarea[required]").count() > 0:
                raise RuntimeError("manual input required")

            break

        raise RuntimeError("unable to complete Easy Apply flow")

    def _dismiss_modal(self, page: Page) -> None:
        dismiss_button = page.locator("button[aria-label='Dismiss']").first
        if dismiss_button.count() > 0:
            dismiss_button.click()
            page.wait_for_timeout(500)
            discard_button = page.locator("button[data-control-name='discard_application_confirm_btn']").first
            if discard_button.count() > 0:
                discard_button.click()

    def _record_application(self, db, listing: JobListing, applied: bool, note: str) -> None:
        existing = db.scalar(select(JobApplication).where(JobApplication.url == listing.url))
        status = JobApplicationStatus.APPLIED if applied else JobApplicationStatus.REJECTED
        now = datetime.now(timezone.utc)

        if existing is None:
            existing = JobApplication(
                job_title=listing.title,
                company=listing.company,
                url=listing.url,
                status=status,
                applied_at=now,
                last_updated=now,
                notes=note,
                platform=JobPlatform.LINKEDIN,
            )
            db.add(existing)
            return

        existing.job_title = listing.title
        existing.company = listing.company
        if applied or existing.status not in {
            JobApplicationStatus.APPLIED,
            JobApplicationStatus.INTERVIEW,
            JobApplicationStatus.OFFER,
        }:
            existing.status = status
        if applied:
            existing.applied_at = now
        existing.last_updated = now
        existing.notes = note
        db.add(existing)

    def _absolute_link(self, href: str) -> str:
        if href.startswith("http"):
            return href
        return f"https://www.linkedin.com{href}"
