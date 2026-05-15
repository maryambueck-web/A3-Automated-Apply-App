import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  downloadApplicationLetterPdf,
  previewApplicationLetter,
  triggerAutomation,
  listJobs,
} from "./api.js";
import { JobsTable } from "./components/JobsTable.jsx";

const statuses = ["all", "applied", "rejected", "interview", "offer"];

const initialLetterForm = {
  job_title: "",
  sender_name: "",
  recipient_name: "",
  company_name: "",
  custom_salutation: "",
  file_name: "",
};

export default function App() {
  const { t, i18n } = useTranslation();
  const [jobs, setJobs] = useState([]);
  const [status, setStatus] = useState("all");
  const [keyword, setKeyword] = useState("");
  const [message, setMessage] = useState("");
  const [letterForm, setLetterForm] = useState(initialLetterForm);
  const [letterPreview, setLetterPreview] = useState("");
  const [isDownloading, setIsDownloading] = useState(false);

  async function loadJobs() {
    const nextJobs = await listJobs(status === "all" ? undefined : status);
    setJobs(nextJobs);
  }

  useEffect(() => {
    loadJobs().catch(() => setJobs([]));
  }, [status]);

  useEffect(() => {
    const hasAnyValue = Object.values(letterForm).some((value) => value.trim() !== "");
    if (!hasAnyValue) {
      setLetterPreview("");
      return undefined;
    }

    const timeoutId = window.setTimeout(async () => {
      try {
        const payload = Object.fromEntries(
          Object.entries(letterForm).map(([key, value]) => [key, value.trim() || null]),
        );
        const result = await previewApplicationLetter(payload);
        setLetterPreview(result.content);
      } catch {
        setLetterPreview("");
      }
    }, 200);

    return () => window.clearTimeout(timeoutId);
  }, [letterForm]);

  async function handleRunAutomation() {
    const result = await triggerAutomation();
    setMessage(result.status === "queued" ? t("queued") : result.status);
  }

  function handleLetterFieldChange(event) {
    const { name, value } = event.target;
    setLetterForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleDownloadLetter(event) {
    event.preventDefault();
    setIsDownloading(true);
    setMessage("");

    try {
      const payload = Object.fromEntries(
        Object.entries(letterForm).map(([key, value]) => [key, value.trim() || null]),
      );

      const { blob, fileName } = await downloadApplicationLetterPdf(payload);
      const downloadUrl = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = downloadUrl;
      anchor.download = fileName;
      anchor.click();
      window.URL.revokeObjectURL(downloadUrl);
      setMessage(t("letterDownloaded"));
    } catch {
      setMessage(t("letterDownloadFailed"));
    } finally {
      setIsDownloading(false);
    }
  }

  const filteredJobs = jobs.filter((job) => {
    const searchValue = keyword.toLowerCase();
    return (
      job.job_title.toLowerCase().includes(searchValue) ||
      job.company.toLowerCase().includes(searchValue)
    );
  });

  return (
    <main className="page-shell">
      <section className="hero-card">
        <div>
          <p className="eyebrow">LinkedIn</p>
          <h1>{t("title")}</h1>
          <p className="subtitle">{t("subtitle")}</p>
        </div>
        <div className="hero-actions">
          <button className="primary-button" onClick={handleRunAutomation}>
            {t("trigger")}
          </button>
          <button className="secondary-button" onClick={() => loadJobs()}>
            {t("refresh")}
          </button>
          <select
            className="language-select"
            value={i18n.language}
            onChange={(event) => i18n.changeLanguage(event.target.value)}
          >
            <option value="en">English</option>
            <option value="de">Deutsch</option>
          </select>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <p className="section-kicker">PDF</p>
            <h2>{t("letterTitle")}</h2>
            <p className="section-copy">{t("letterSubtitle")}</p>
          </div>
        </div>
        <form className="letter-form" onSubmit={handleDownloadLetter}>
          <label className="field-group">
            <span>{t("jobTitle")}</span>
            <input
              className="text-input"
              name="job_title"
              value={letterForm.job_title}
              onChange={handleLetterFieldChange}
              required
            />
          </label>
          <label className="field-group">
            <span>{t("senderName")}</span>
            <input
              className="text-input"
              name="sender_name"
              value={letterForm.sender_name}
              onChange={handleLetterFieldChange}
              required
            />
          </label>
          <label className="field-group">
            <span>{t("recipientName")}</span>
            <input
              className="text-input"
              name="recipient_name"
              value={letterForm.recipient_name}
              onChange={handleLetterFieldChange}
            />
          </label>
          <label className="field-group">
            <span>{t("company")}</span>
            <input
              className="text-input"
              name="company_name"
              value={letterForm.company_name}
              onChange={handleLetterFieldChange}
            />
          </label>
          <label className="field-group field-group-wide">
            <span>{t("customSalutation")}</span>
            <input
              className="text-input"
              name="custom_salutation"
              placeholder={t("customSalutationPlaceholder")}
              value={letterForm.custom_salutation}
              onChange={handleLetterFieldChange}
            />
          </label>
          <label className="field-group field-group-wide">
            <span>{t("fileName")}</span>
            <input
              className="text-input"
              name="file_name"
              placeholder={t("fileNamePlaceholder")}
              value={letterForm.file_name}
              onChange={handleLetterFieldChange}
            />
          </label>
          <div className="letter-actions">
            <button className="primary-button" type="submit" disabled={isDownloading}>
              {isDownloading ? t("downloading") : t("downloadLetter")}
            </button>
          </div>
        </form>
        <div className="preview-shell">
          <div className="preview-header">
            <h3>{t("letterPreviewTitle")}</h3>
            <p>{t("letterPreviewSubtitle")}</p>
          </div>
          {letterPreview ? (
            <pre className="letter-preview">{letterPreview}</pre>
          ) : (
            <p className="preview-empty">{t("letterPreviewEmpty")}</p>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="filter-row">
          <input
            className="text-input"
            placeholder={t("keyword")}
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
          />
          <select className="text-input" value={status} onChange={(event) => setStatus(event.target.value)}>
            {statuses.map((entry) => (
              <option key={entry} value={entry}>
                {entry === "all" ? t("all") : entry}
              </option>
            ))}
          </select>
        </div>
        {message ? <p className="status-banner">{message}</p> : null}
        <JobsTable jobs={filteredJobs} emptyLabel={t("empty")} />
      </section>
    </main>
  );
}
