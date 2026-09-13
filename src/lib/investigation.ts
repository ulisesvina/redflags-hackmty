export type AttachedBook = { id: string; name: string; size: number; file: File };
export type ExtractedEntry = { date?: string; description?: string; amount?: number; currency?: string; source?: string };
export type WorkflowState = "EMPTY" | "CHECKING" | "INSUFFICIENT_DATA" | "ANALYZING" | "ANALYZED" | "ERROR";

export type Readiness = {
  ready: boolean;
  requiredFiles: string[];
  presentFiles: string[];
  missingFiles: string[];
};

export type Entity = { id: string; name: string; rfc: string; kind: string; detail: string; account?: string };
export type Finding = {
  id: string;
  schemeType: string;
  title: string;
  rule: string;
  amountMxn: number;
  confidence: string;
  confidenceScore: number;
  narrative: string;
  accused: Entity[];
  evidenceIds: string[];
};
export type EvidenceItem = {
  id: string;
  source: string;
  file: string;
  date: string;
  amountMxn: number | null;
  description: string;
};
export type MoneyNode = { id: string; label: string; detail: string; kind: string; risk: boolean };
export type MoneyEdge = { from: string; to: string; amountMxn: number; label: string; evidenceIds: string[] };
export type Presentation = {
  company: { name?: string; rfc?: string; city?: string };
  status: "fraud_found" | "clean";
  headline: string;
  summary: string;
  totalExposureMxn: number;
  confidence: number;
  findings: Finding[];
  evidence: EvidenceItem[];
  affectedSuppliers: Array<Entity & { exposureMxn: number; basis: string }>;
  leadsNotPursued: Array<{ entity: string; entityId?: string; reason: string; closedBy?: string }>;
  moneyFlow: { nodes: MoneyNode[]; edges: MoneyEdge[] };
  timeline: Array<{ step: number; kind: string; entityId: string; detail: string; accepted?: boolean }>;
  recordCounts: { invoices: number; bank: number; suppliers: number; evidence: number };
};
export type Integrity = { algorithm: "SHA-256"; hash: string; status: "local" | "anchored"; network?: string; signature?: string; explorerUrl?: string; error?: string };
export type Extraction = {
  caseId: string;
  companyName: string | null;
  filesReceived: number;
  entries: ExtractedEntry[];
  runId: string;
  readiness: Readiness;
};
export type Investigation = {
  investigationId: string;
  status: "complete";
  case: { findings?: unknown[]; not_pursued?: unknown[] };
  presentation: Presentation;
  integrity: Integrity;
};
export type Integration = {
  id: "gemini" | "mongodb" | "vultr" | "solana";
  name: string;
  configured: boolean;
  state: "live" | "fallback" | "deploy-ready";
  role: string;
  fallback: string;
};

export const ACCEPTED_BOOKS = ".zip,.csv,.json,.pdf,.xlsx,.xls";
export const REQUIRED_GROUPS = [
  { title: "Company & parties", files: ["company.json", "suppliers.csv", "customers.csv", "employees.csv"] },
  { title: "Invoices & delivery", files: ["invoices.csv", "goods_receipts.csv"] },
  { title: "Money movement", files: ["bank_transactions.csv", "counterparty_bank.csv"] },
  { title: "Books & tax screen", files: ["ledger.csv", "efos_69b.csv"] },
];

export function buildBookList(current: AttachedBook[], incoming: File[]): AttachedBook[] {
  const accepted = ACCEPTED_BOOKS.split(",");
  const additions = incoming
    .filter((file) => accepted.some((extension) => file.name.toLowerCase().endsWith(extension)))
    .map((file) => ({ id: `${file.name}-${file.size}-${file.lastModified}`, name: file.name, size: file.size, file }));
  return [...new Map([...current, ...additions].map((book) => [book.id, book])).values()];
}

export function readinessProgress(readiness?: Readiness) {
  if (!readiness?.requiredFiles.length) return 0;
  return Math.round((readiness.presentFiles.length / readiness.requiredFiles.length) * 100);
}

export function groupReadiness(readiness: Readiness | undefined) {
  const present = new Set(readiness?.presentFiles ?? []);
  return REQUIRED_GROUPS.map((group) => ({
    ...group,
    present: group.files.filter((file) => present.has(file)).length,
    complete: group.files.every((file) => present.has(file)),
    missing: group.files.filter((file) => !present.has(file)),
  }));
}

export function formatMxn(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "MXN", maximumFractionDigits: 2 }).format(value);
}

export function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
