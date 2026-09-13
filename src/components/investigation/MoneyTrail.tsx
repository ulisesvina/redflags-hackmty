import { ArrowRight, Building2, Network, UserRound } from "lucide-react";
import type { MoneyEdge, MoneyNode } from "@/lib/investigation";
import { formatMxn } from "@/lib/investigation";

function nodeIcon(kind: string) {
  if (kind === "employee") return <UserRound size={14} />;
  if (kind === "company") return <Building2 size={14} />;
  return <Network size={14} />;
}

function FlowNode({ node }: { node?: MoneyNode }) {
  if (!node) return <div />;
  return <div className={`rf-flow-node ${node.risk ? "risk" : ""}`}><i>{nodeIcon(node.kind)}</i><span><strong>{node.label}</strong><small>{node.detail}</small></span>{node.risk && <em>Evidence linked</em>}</div>;
}

export function MoneyTrail({ nodes, edges, clean }: { nodes: MoneyNode[]; edges: MoneyEdge[]; clean: boolean }) {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  return (
    <div className={`rf-money-trail ${clean ? "clean" : ""}`}>
      <div className="rf-flow-legend"><span><i /> Reconciled bank path</span>{!clean && <span><b /> Accusation supported</span>}</div>
      <div className="rf-flow-list">
        {edges.map((edge, index) => <div className="rf-flow-row" key={`${edge.from}-${edge.to}-${index}`}>
          <FlowNode node={nodeMap.get(edge.from)} />
          <div className="rf-flow-edge"><strong>{edge.amountMxn ? formatMxn(edge.amountMxn) : "Tests complete"}</strong><span><i /><ArrowRight size={15} /></span><small>{edge.label} · {edge.evidenceIds.length} cited records</small></div>
          <FlowNode node={nodeMap.get(edge.to)} />
        </div>)}
      </div>
    </div>
  );
}
