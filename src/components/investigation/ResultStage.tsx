"use client";

import { AlertTriangle, ArrowUpRight, Check, Download, FileCheck2, Link2, MessageCircleQuestion, RefreshCcw, Scale, ShieldCheck, Sparkles, X } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";
import type { Integration, Integrity, Investigation } from "@/lib/investigation";
import { formatMxn } from "@/lib/investigation";
import { anchorCase, askCase } from "@/lib/redflags-api";
import { MoneyTrail } from "./MoneyTrail";
import { IntegrationPanel } from "./IntegrationPanel";

export function ResultStage({ investigation, integrations, onReset }: { investigation: Investigation; integrations: Integration[]; onReset: () => void }) {
  const { presentation } = investigation;
  const fraud = presentation.status === "fraud_found";
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [provider, setProvider] = useState("");
  const [asking, setAsking] = useState(false);
  const [integrity, setIntegrity] = useState<Integrity>(investigation.integrity);
  const [anchoring, setAnchoring] = useState(false);
  const [notice, setNotice] = useState("");

  async function submitQuestion(value = question) {
    if (!value.trim()) return;
    setQuestion(value);
    setAsking(true);
    try {
      const result = await askCase(investigation.investigationId, value);
      setAnswer(result.answer);
      setProvider(result.provider);
    } catch (error) {
      setAnswer(error instanceof Error ? error.message : "The case could not answer that question.");
      setProvider("Unavailable");
    } finally { setAsking(false); }
  }

  async function anchor() {
    setAnchoring(true);
    setNotice("");
    try {
      const proof = await anchorCase(investigation.investigationId);
      setIntegrity(proof);
      setNotice(proof.status === "anchored" ? "Evidence manifest anchored on Solana devnet." : proof.error ?? "Local SHA-256 proof is locked. Add a funded devnet key to notarize it on-chain.");
    } catch (error) { setNotice(error instanceof Error ? error.message : "The proof could not be anchored."); }
    finally { setAnchoring(false); }
  }

  function download() {
    const body = JSON.stringify({ ...investigation, integrity }, null, 2);
    const href = URL.createObjectURL(new Blob([body], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = href;
    link.download = `case-${investigation.investigationId}.json`;
    link.click();
    URL.revokeObjectURL(href);
  }

  return (
    <section className={`rf-result ${fraud ? "fraud" : "clean"} rf-stage-enter`} data-testid={fraud ? "fraud-result" : "clean-result"}>
      <div className="rf-verdict">
        <div className="rf-verdict-meta"><span>CASE · {investigation.investigationId.slice(0, 12).toUpperCase()}</span></div>
        <div className="rf-verdict-main">
          <i>{fraud ? <AlertTriangle size={28} /> : <Check size={28} />}</i>
          <div><span className="rf-kicker">{fraud ? "ACCUSATION THRESHOLD CROSSED" : "INVESTIGATION COMPLETE"}</span><h1>{presentation.headline}</h1><p>{presentation.summary}</p></div>
          <div className="rf-confidence"><strong>{presentation.confidence}%</strong><span>case confidence</span></div>
        </div>
        <div className="rf-verdict-actions"><button className="rf-button rf-button-outline" onClick={download}><Download size={13} /> Export</button><button className="rf-button rf-button-quiet" onClick={onReset}><RefreshCcw size={13} /> New case</button></div>
        {notice && <p className="rf-action-notice" role="status">{notice}</p>}
      </div>

      <div className="rf-metrics">
        <article className="primary"><small>SUPPORTED EXPOSURE</small><strong>{formatMxn(presentation.totalExposureMxn)}</strong><span>{fraud ? "Validated findings only" : "No supported fraud"}</span></article>
        <article><small>FINDINGS</small><strong>{presentation.findings.length}</strong><span>Validated</span></article>
        <article><small>RECORDS</small><strong>{presentation.recordCounts.evidence}</strong><span>Cited</span></article>
        <article><small>CLOSED LEADS</small><strong>{presentation.leadsNotPursued.length}</strong><span>Not accused</span></article>
      </div>

      <CaseSection index="01" eyebrow="MONEY TRAIL" title={fraud ? "The peso path, end to end" : "Reconciled estate with no provable scheme"} aside={fraud ? "Each hop cites source records" : "No circular flow crossed the threshold"}>
        <MoneyTrail nodes={presentation.moneyFlow.nodes} edges={presentation.moneyFlow.edges} clean={!fraud} />
      </CaseSection>

      <div className="rf-result-columns">
        <CaseSection index="02" eyebrow="FINDINGS" title={fraud ? "Supported findings" : "No accusation"}>
          {fraud ? <div className="rf-finding-list">{presentation.findings.map((finding) => <article className="rf-finding" key={finding.id}><div><span>{finding.id}</span><strong>{finding.title}</strong><em>{formatMxn(finding.amountMxn)}</em></div><p>{finding.narrative}</p><small><Scale size={12} /><span><b>RULE APPLIED</b>{finding.rule}</span></small><footer><span>{finding.confidenceScore}% · {finding.confidence}</span><span>{finding.evidenceIds.length} cited records</span></footer></article>)}</div> : <div className="rf-clean-callout"><i><ShieldCheck size={24} /></i><h3>The evidence bar held.</h3><p>Exceptions were investigated, but no party had the required combination of a broken rule, verified record IDs and a defensible paid-peso amount.</p></div>}
        </CaseSection>
        <CaseSection index="03" eyebrow="AFFECTED PARTIES" title={fraud ? "Named only with support" : "Suppliers remain unaccused"}>
          {presentation.affectedSuppliers.length ? <div className="rf-supplier-list">{presentation.affectedSuppliers.map((supplier) => <article key={supplier.id}><i>{supplier.name.split(" ").slice(0, 2).map((part) => part[0]).join("")}</i><span><strong>{supplier.name}</strong><small>{supplier.id} · RFC {supplier.rfc}</small><p>{supplier.basis}</p></span><em>{formatMxn(supplier.exposureMxn)}</em></article>)}</div> : <div className="rf-empty-result"><Check size={25} /><strong>No supplier crossed the threshold</strong><span>Potential exceptions remain visible in the judgment log below.</span></div>}
        </CaseSection>
      </div>

      <CaseSection index="04" eyebrow="EVIDENCE TRAIL" title="Every claim points back to a source" aside={`${presentation.evidence.length} locked record IDs`}>
        {presentation.evidence.length ? <div className="rf-evidence-table">{presentation.evidence.slice(0, 12).map((item) => <div key={item.id}><code>{item.id}</code><span><strong>{item.source}</strong><small>{item.file} {item.date && `· ${item.date}`}</small></span><p>{item.description}</p><em>{item.amountMxn ? formatMxn(item.amountMxn) : "Verified"}</em></div>)}{presentation.evidence.length > 12 && <p className="rf-table-more">+ {presentation.evidence.length - 12} additional cited records preserved in the exported case file</p>}</div> : <div className="rf-empty-line"><FileCheck2 size={16} /> No accusatory evidence bundle was created for this clean result.</div>}
      </CaseSection>

      <CaseSection index="05" eyebrow="JUDGMENT LOG" title="Leads deliberately not pursued" aside="Anomaly ≠ accusation">
        <div className="rf-leads">{presentation.leadsNotPursued.slice(0, 6).map((lead, index) => <article key={`${lead.entity}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span><div><strong>{lead.entity}</strong><p>{lead.reason}</p><small><X size={10} /> Not accused · insufficient corroboration</small></div></article>)}{presentation.leadsNotPursued.length === 0 && <div className="rf-empty-line"><Check size={15} /> No abandoned lead required an additional judgment note.</div>}</div>
      </CaseSection>

      <section className="rf-qa-section">
        <div><span className="rf-kicker">06 / CASE Q&amp;A</span><h2>Ask about the result.</h2><p>Answers use this case only.</p></div>
        <div className="rf-qa-panel"><label htmlFor="rf-question">SURPRISE QUESTION</label><div><MessageCircleQuestion size={16} /><input id="rf-question" value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => event.key === "Enter" && void submitQuestion()} placeholder="Why are you confident this is fraud?" /><button onClick={() => void submitQuestion()} disabled={asking || !question.trim()}>{asking ? "Thinking..." : "Ask"}</button></div>{answer ? <article className="rf-answer"><ShieldCheck size={16} /><p>{answer}</p><small>Answered by {provider} · finalized evidence only</small></article> : <aside>{["What exact amount can you prove?", "Why not accuse the other suppliers?", "What evidence supports this?"].map((prompt) => <button key={prompt} onClick={() => void submitQuestion(prompt)}>{prompt}</button>)}</aside>}</div>
      </section>

      <section className="rf-integrity"><span><i><Link2 size={17} /></i><span><small>EVIDENCE INTEGRITY</small><strong>{integrity.status === "anchored" ? "Manifest notarized on Solana" : "Case fingerprint finalized"}</strong><code>SHA-256 · {integrity.hash}</code></span></span>{integrity.status === "anchored" && integrity.explorerUrl ? <a className="rf-button rf-button-outline" target="_blank" rel="noreferrer" href={integrity.explorerUrl}>View on Solana <ArrowUpRight size={13} /></a> : <button className="rf-button rf-button-outline" onClick={() => void anchor()} disabled={anchoring}>{anchoring ? "Anchoring..." : "Anchor on Solana devnet"} <Link2 size={12} /></button>}</section>
    </section>
  );
}

function CaseSection({ index, eyebrow, title, aside, children }: { index: string; eyebrow: string; title: string; aside?: string; children: ReactNode }) {
  return <section className="rf-case-section"><div className="rf-section-heading"><span><small>{index} / {eyebrow}</small><h2>{title}</h2></span>{aside && <p>{aside}</p>}</div>{children}</section>;
}
