import { Check, Paperclip, ShieldCheck } from "lucide-react";
import type { WorkflowState } from "@/lib/investigation";
import { ACCEPTED_BOOKS } from "@/lib/investigation";
import type { ChangeEvent } from "react";

const steps: Array<{ id: WorkflowState; label: string }> = [
  { id: "EMPTY", label: "Upload" },
  { id: "INSUFFICIENT_DATA", label: "Check" },
  { id: "ANALYZING", label: "Analyze" },
  { id: "ANALYZED", label: "Result" },
];

function progressIndex(state: WorkflowState) {
  if (state === "CHECKING") return 1;
  if (state === "ERROR") return 1;
  return Math.max(0, steps.findIndex((step) => step.id === state));
}

export function InvestigationHeader({
  state, companyName, caseId, userName, onFiles,
}: {
  state: WorkflowState;
  companyName?: string | null;
  caseId?: string;
  userName: string;
  onFiles: (event: ChangeEvent<HTMLInputElement>) => void;
}) {
  const active = progressIndex(state);
  return (
    <header className="rf-header">
        <div className="rf-brand">🚩 redflags</div>
        <nav className="rf-progress" aria-label="Investigation progress">
          {steps.map((step, index) => (
            <span className={index < active ? "done" : index === active ? "active" : ""} key={step.id}>
              <i>{index < active ? <Check size={10} /> : index + 1}</i>{step.label}
            </span>
          ))}
        </nav>
        <div className="rf-header-actions">
          {companyName && <span className="rf-current-case"><small>{caseId ?? "CURRENT CASE"}</small><strong>{companyName}</strong></span>}
          {userName && <span className="rf-user">{userName}</span>}
          <label className="rf-button rf-button-outline"><Paperclip size={13} /> Add books<input hidden multiple type="file" accept={ACCEPTED_BOOKS} onChange={onFiles} /></label>
        </div>
    </header>
  );
}
