"use client";

import { AlertTriangle, X } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { AnalyzingStage } from "@/components/investigation/AnalyzingStage";
import { IntakeStage } from "@/components/investigation/IntakeStage";
import { InvestigationHeader } from "@/components/investigation/InvestigationHeader";
import { ReadinessStage } from "@/components/investigation/ReadinessStage";
import { ResultStage } from "@/components/investigation/ResultStage";
import type { AttachedBook, Extraction, Integration, Investigation, WorkflowState } from "@/lib/investigation";
import { buildBookList } from "@/lib/investigation";
import { getIntegrations, loadDemoBook, startInvestigation, uploadBooks } from "@/lib/redflags-api";

const fallbackIntegrations: Integration[] = [
  { id: "gemini", name: "Gemini", configured: false, state: "fallback", role: "Case Q&A", fallback: "Local answers" },
  { id: "mongodb", name: "MongoDB", configured: false, state: "fallback", role: "Case storage", fallback: "Local storage" },
  { id: "vultr", name: "Vultr", configured: false, state: "deploy-ready", role: "Cloud deployment", fallback: "Runs locally" },
  { id: "solana", name: "Solana", configured: false, state: "fallback", role: "Evidence timestamp", fallback: "Local SHA-256" },
];

export default function DashboardPage() {
  return <Suspense fallback={<main className="rf-app" />}><Dashboard /></Suspense>;
}

function Dashboard() {
  const searchParams = useSearchParams();
  const userName = searchParams.get("userName")?.trim() ?? "";
  const token = "redflags-demo-session";
  const [books, setBooks] = useState<AttachedBook[]>([]);
  const [extraction, setExtraction] = useState<Extraction | null>(null);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [state, setState] = useState<WorkflowState>("EMPTY");
  const [dragging, setDragging] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [error, setError] = useState("");
  const [integrations, setIntegrations] = useState<Integration[]>(fallbackIntegrations);

  useEffect(() => {
    getIntegrations().then((result) => setIntegrations(result.integrations)).catch(() => undefined);
  }, []);

  async function processBooks(nextBooks: AttachedBook[]) {
    if (!nextBooks.length) { reset(); return; }
    setBooks(nextBooks);
    setInvestigation(null);
    setError("");
    setState("CHECKING");
    try {
      const extracted = await uploadBooks(nextBooks, token);
      setExtraction(extracted);
      if (!extracted.readiness.ready) {
        setState("INSUFFICIENT_DATA");
        return;
      }
      setState("ANALYZING");
      const started = Date.now();
      const result = await startInvestigation(extracted.runId, token);
      const minimumStageTime = Math.max(0, 2_400 - (Date.now() - started));
      await new Promise((resolve) => window.setTimeout(resolve, minimumStageTime));
      setInvestigation(result);
      setState("ANALYZED");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The investigation service is unavailable.");
      setState("ERROR");
    }
  }

  function addFiles(files: File[]) {
    const next = buildBookList(books, files);
    if (next.length === books.length) {
      setError("Use a ZIP, CSV, JSON, PDF, XLSX or XLS accounting file.");
      return;
    }
    void processBooks(next);
  }

  function handleInput(event: ChangeEvent<HTMLInputElement>) {
    addFiles(Array.from(event.target.files ?? []));
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    setDragging(false);
    addFiles(Array.from(event.dataTransfer.files));
  }

  async function loadDemo(scenario: "fraud" | "clean") {
    setLoadingDemo(true);
    setError("");
    try {
      const file = await loadDemoBook(scenario);
      await processBooks(buildBookList([], [file]));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The demo could not be loaded.");
      setState("ERROR");
    } finally { setLoadingDemo(false); }
  }

  function removeBook(id: string) {
    void processBooks(books.filter((book) => book.id !== id));
  }

  function reset() {
    setBooks([]);
    setExtraction(null);
    setInvestigation(null);
    setError("");
    setState("EMPTY");
  }

  const companyName = investigation?.presentation.company.name ?? extraction?.companyName;
  return (
    <main className="rf-app">
      <InvestigationHeader state={state} companyName={companyName} caseId={extraction?.caseId} userName={userName} onFiles={handleInput} />
      {error && <div className="rf-error" role="alert"><AlertTriangle size={14} /><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError("")}><X size={13} /></button></div>}
      {state === "EMPTY" && <IntakeStage dragging={dragging} loadingDemo={loadingDemo} onDrag={(event) => { event.preventDefault(); setDragging(true); }} onLeave={() => setDragging(false)} onDrop={handleDrop} onFiles={handleInput} onDemo={loadDemo} />}
      {(state === "CHECKING" || state === "INSUFFICIENT_DATA" || state === "ERROR") && books.length > 0 && <ReadinessStage books={books} extraction={extraction} checking={state === "CHECKING"} dragging={dragging} onDrag={(event) => { event.preventDefault(); setDragging(true); }} onLeave={() => setDragging(false)} onDrop={handleDrop} onFiles={handleInput} onRemove={removeBook} />}
      {state === "ANALYZING" && <AnalyzingStage companyName={companyName} />}
      {state === "ANALYZED" && investigation && <ResultStage investigation={investigation} integrations={integrations} onReset={reset} />}
    </main>
  );
}
