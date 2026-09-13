import type { AttachedBook, Extraction, Integration, Integrity, Investigation } from "./investigation";

const API_URL = process.env.NEXT_PUBLIC_REDFLAGS_API_URL ?? "/api/redflags";

async function parse<T>(response: Response): Promise<T> {
  const payload = await response.json();
  if (!response.ok) {
    const detail = payload.detail;
    const message = typeof detail === "string" ? detail : detail?.reason ? `${detail.message}: ${detail.reason}` : detail?.message;
    throw new Error(message || "The request could not be completed.");
  }
  return payload as T;
}

export async function uploadBooks(books: AttachedBook[], token: string) {
  const body = new FormData();
  books.forEach((book) => body.append("books", book.file));
  return parse<Extraction>(await fetch(`${API_URL}/extract-books`, {
    method: "POST", headers: { Authorization: `Bearer ${token}` }, body,
  }));
}

export async function startInvestigation(runId: string, token: string) {
  return parse<Investigation>(await fetch(`${API_URL}/investigate/start`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ runId }),
  }));
}

export async function loadDemoBook(scenario: "fraud" | "clean") {
  const response = await fetch(`${API_URL}/demo-books/${scenario}`);
  if (!response.ok) throw new Error("The demo case is unavailable.");
  const blob = await response.blob();
  const name = scenario === "fraud" ? "fraud-case.zip" : "clean-case.zip";
  return new File([blob], name, { type: "application/zip", lastModified: Date.now() });
}

export async function getIntegrations() {
  return parse<{ integrations: Integration[] }>(await fetch(`${API_URL}/integrations/status`));
}

export async function askCase(runId: string, question: string) {
  return parse<{ answer: string; provider: string }>(await fetch(`${API_URL}/cases/${runId}/ask`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }),
  }));
}

export async function anchorCase(runId: string) {
  return parse<Integrity>(await fetch(`${API_URL}/cases/${runId}/anchor`, { method: "POST" }));
}
