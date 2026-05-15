from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


APPLICATION_LETTER_TEMPLATE = """Application for the position of {job_title}

{salutation}

I am writing to apply for the position of {job_title} at {company_reference} with great interest. I am looking for a professional opportunity where I can prove myself, continue learning, and become a reliable long-term member of your team.

Although I do not yet have many years of experience in this field, I bring a high level of motivation, willingness to learn, and perseverance. I learn quickly, take new tasks seriously, and do not give up until I have achieved my goal. This is exactly the attitude I would like to bring to your company.

I am reliable, punctual, resilient, and ready to familiarize myself intensively with new responsibilities. It is important to me not only to find a job, but also to develop professionally and provide real added value to my employer.

An additional advantage for your company could be a possible integration subsidy. Through the Federal Employment Agency or the Jobcenter, it can be checked whether my employment may be financially supported. A corresponding funding check can be carried out easily and could make your decision even easier.

I would be very pleased to have the opportunity to introduce myself personally and convince you of my motivation.

Yours sincerely,

{sender_name}
"""


@dataclass(slots=True)
class ApplicationLetterContext:
    job_title: str
    sender_name: str
    recipient_name: str | None = None
    company_name: str | None = None
    custom_salutation: str | None = None

    @property
    def salutation(self) -> str:
        if self.custom_salutation:
            return self.custom_salutation.strip()
        if self.recipient_name:
            return f"Dear Ms./Mr. {self.recipient_name.strip()},"
        return "Dear Sir or Madam,"

    @property
    def company_reference(self) -> str:
        if self.company_name:
            return self.company_name.strip()
        return "your company"


def render_application_letter(context: ApplicationLetterContext) -> str:
    return APPLICATION_LETTER_TEMPLATE.format(
        job_title=context.job_title.strip(),
        salutation=context.salutation,
        company_reference=context.company_reference,
        sender_name=context.sender_name.strip(),
    )


def render_application_letter_pdf_bytes(context: ApplicationLetterContext) -> bytes:
    buffer = BytesIO()
    _write_application_letter_pdf(context, buffer)
    return buffer.getvalue()


def export_application_letter_pdf(
    context: ApplicationLetterContext,
    output_path: str | Path,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("wb") as output_file:
        _write_application_letter_pdf(context, output_file)

    return destination


def _write_application_letter_pdf(context: ApplicationLetterContext, target) -> None:
    pdf = canvas.Canvas(target, pagesize=A4)
    page_width, page_height = A4
    left_margin = 72
    right_margin = 72
    top_margin = 72
    bottom_margin = 72
    line_height = 16
    font_name = "Times-Roman"
    font_size = 12
    usable_width = page_width - left_margin - right_margin

    def new_text_object():
        text_object = pdf.beginText(left_margin, page_height - top_margin)
        text_object.setFont(font_name, font_size)
        return text_object

    text = new_text_object()

    def ensure_space() -> None:
        nonlocal text
        if text.getY() <= bottom_margin:
            pdf.drawText(text)
            pdf.showPage()
            text = new_text_object()

    for paragraph in render_application_letter(context).split("\n\n"):
        for raw_line in paragraph.splitlines() or [""]:
            wrapped_lines = simpleSplit(raw_line, font_name, font_size, usable_width) or [""]
            for wrapped_line in wrapped_lines:
                ensure_space()
                text.textLine(wrapped_line)
        ensure_space()
        text.moveCursor(0, line_height)

    pdf.drawText(text)
    pdf.save()


EXAMPLE_APPLICATION_LETTER_CONTEXT = ApplicationLetterContext(
    job_title="Software Engineer",
    sender_name="Your Name",
    recipient_name="Name",
    company_name="the company",
)