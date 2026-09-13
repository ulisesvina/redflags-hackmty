import { Check, Cloud, Database, Link2, Sparkles } from "lucide-react";
import type { Integration } from "@/lib/investigation";

const icons = { gemini: Sparkles, mongodb: Database, vultr: Cloud, solana: Link2 };

export function IntegrationPanel({ integrations }: { integrations: Integration[] }) {
  return <div className="rf-integration-grid">{integrations.map((item) => {
    const Icon = icons[item.id];
    return <article className="rf-integration" key={item.id}><div><i className={item.id}><Icon size={15} /></i><span className={`rf-integration-state ${item.state}`}>{item.configured && <Check size={9} />}{item.state === "live" ? "Live" : item.state === "deploy-ready" ? "Ready" : "Optional"}</span></div><h3>{item.name}</h3><p>{item.role}</p><small>{item.configured ? "Connected" : item.fallback}</small></article>;
  })}</div>;
}
