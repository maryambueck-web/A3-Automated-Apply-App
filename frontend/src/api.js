const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "change-me";

async function request(path, init = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...(init.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function listJobs(status) {
  const query = status ? `?status=${status}` : "";
  return request(`/jobs${query}`);
}

export function triggerAutomation() {
  return request("/automation/run", { method: "POST" });
}

export function previewApplicationLetter(payload) {
  return request("/automation/application-letter/preview", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function downloadApplicationLetterPdf(payload) {
  const response = await fetch(`${API_BASE_URL}/automation/application-letter/pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const blob = await response.blob();
  const fileName = response.headers.get("content-disposition")?.match(/filename="?([^\"]+)"?/)?.[1] ?? "application-letter.pdf";
  return { blob, fileName };
}
