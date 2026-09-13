"use client";

import { Check, Database, FileCheck2, GitBranch, LoaderCircle, Search, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

const stages = [
  { label: "Sources loaded", detail: "Ledger, invoices, bank and suppliers", Icon: Database },
  { label: "Leads ranked", detail: "Tax, reconciliation and anomaly checks", Icon: Search },
  { label: "Money traced", detail: "Linking payments and accounts", Icon: GitBranch },
  { label: "Evidence tested", detail: "Dropping unsupported leads", Icon: ShieldCheck },
  { label: "Result locked", detail: "Validating records and amounts", Icon: FileCheck2 },
];

export function AnalyzingStage({ companyName }: { companyName?: string | null }) {
  const [active, setActive] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => setActive((value) => Math.min(stages.length - 1, value + 1)), 520);
    return () => window.clearInterval(timer);
  }, []);
  return (
    <section className="rf-analyzing rf-stage-enter">
      <div className="rf-analysis-visual"><div className="rf-orbit"><span /><span /><span /><i><Search size={25} /></i></div><span className="rf-kicker">Analysis</span><h1>Following the money.</h1><p>{companyName ?? "Uploaded company"}</p></div>
      <div className="rf-analysis-list">
        {stages.map(({ label, detail, Icon }, index) => <div className={index < active ? "complete" : index === active ? "active" : ""} key={label}><i>{index < active ? <Check size={14} /> : <Icon size={15} />}</i><span><strong>{label}</strong><small>{detail}</small></span>{index === active && <LoaderCircle className="rf-spin" size={15} />}</div>)}
      </div>
    </section>
  );
}
