import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Integration, Investigation, Presentation } from "@/lib/investigation";
import { ResultStage } from "./ResultStage";

const integrations: Integration[] = [
  { id: "gemini", name: "Gemini", configured: false, state: "fallback", role: "Case Q&A", fallback: "Local answers" },
  { id: "mongodb", name: "MongoDB", configured: false, state: "fallback", role: "Storage", fallback: "Local case" },
  { id: "vultr", name: "Vultr", configured: false, state: "deploy-ready", role: "Deployment", fallback: "Local containers" },
  { id: "solana", name: "Solana", configured: false, state: "fallback", role: "Integrity", fallback: "Local SHA-256" },
];

function presentation(status: "fraud_found" | "clean"): Presentation {
  const fraud = status === "fraud_found";
  return {
    company: { name: "Lumen Norte S.A. de C.V.", rfc: "LNO010101AA1", city: "Monterrey" },
    status,
    headline: fraud ? "Supported fraud found" : "No provable fraud found",
    summary: fraud ? "One evidence-backed scheme was proved." : "No allegation crossed the evidence bar.",
    totalExposureMxn: fraud ? 1972000 : 0,
    confidence: fraud ? 97 : 93,
    findings: fraud ? [{ id: "F-01", schemeType: "efos_fake_supplier", title: "Fake supplier on the SAT 69-B list", rule: "R1", amountMxn: 1972000, confidence: "proven", confidenceScore: 97, narrative: "The paid CFDIs reconcile to a listed supplier.", accused: [], evidenceIds: ["INV-1", "TXN-1"] }] : [],
    evidence: fraud ? [{ id: "INV-1", source: "CFDI invoice", file: "invoices.csv", date: "2026-03-01", amountMxn: 1972000, description: "Paid invoice" }] : [],
    affectedSuppliers: fraud ? [{ id: "S-1", name: "Proveedor Uno", rfc: "PRU010101AA1", kind: "supplier", detail: "Services", exposureMxn: 1972000, basis: "R1" }] : [],
    leadsNotPursued: [{ entity: "Proveedor Dos (S-2)", entityId: "S-2", reason: "No corroborating payment path." }],
    moneyFlow: fraud ? {
      nodes: [{ id: "COMPANY", label: "Lumen Norte", detail: "Company", kind: "company", risk: false }, { id: "S-1", label: "Proveedor Uno", detail: "Supplier", kind: "supplier", risk: true }],
      edges: [{ from: "COMPANY", to: "S-1", amountMxn: 1972000, label: "Paid CFDIs", evidenceIds: ["INV-1", "TXN-1"] }],
    } : {
      nodes: [{ id: "COMPANY", label: "Lumen Norte", detail: "Company", kind: "company", risk: false }, { id: "CLEARED", label: "Reconciled counterparties", detail: "No accusation", kind: "supplier", risk: false }],
      edges: [{ from: "COMPANY", to: "CLEARED", amountMxn: 0, label: "Evidence tests completed", evidenceIds: [] }],
    },
    timeline: [],
    recordCounts: { invoices: 10, bank: 12, suppliers: 4, evidence: fraud ? 2 : 0 },
  };
}

function investigation(status: "fraud_found" | "clean"): Investigation {
  return {
    investigationId: `demo-${status}`,
    status: "complete",
    case: { findings: [], not_pursued: [] },
    presentation: presentation(status),
    integrity: { algorithm: "SHA-256", hash: "a".repeat(64), status: "local" },
  };
}

describe("analyzed result", () => {
  it("renders the fraud verdict, peso exposure, money flow and evidence", () => {
    render(<ResultStage investigation={investigation("fraud_found")} integrations={integrations} onReset={() => undefined} />);
    expect(screen.getByTestId("fraud-result")).toBeInTheDocument();
    expect(screen.getByText("Supported fraud found")).toBeInTheDocument();
    expect(screen.getAllByText(/MX\$1,972,000\.00/).length).toBeGreaterThan(0);
    expect(screen.getByText("Paid invoice")).toBeInTheDocument();
    expect(screen.getAllByText("Proveedor Uno").length).toBeGreaterThan(0);
  });

  it("renders a clean verdict without accusing a supplier", () => {
    render(<ResultStage investigation={investigation("clean")} integrations={integrations} onReset={() => undefined} />);
    expect(screen.getByTestId("clean-result")).toBeInTheDocument();
    expect(screen.getByText("No provable fraud found")).toBeInTheDocument();
    expect(screen.getByText("No supplier crossed the threshold")).toBeInTheDocument();
    expect(screen.getByText(/The evidence bar held/)).toBeInTheDocument();
  });
});
