import { Check, FileJson, FileSpreadsheet, LoaderCircle, Trash2, Upload, X } from "lucide-react";
import type { AttachedBook, Extraction } from "@/lib/investigation";
import { ACCEPTED_BOOKS, formatBytes, groupReadiness, readinessProgress } from "@/lib/investigation";
import type { ChangeEvent, DragEvent } from "react";

function FileIcon({ name }: { name: string }) {
  return name.endsWith(".json") ? <FileJson size={16} /> : <FileSpreadsheet size={16} />;
}

export function ReadinessStage({
  books, extraction, checking, dragging, onFiles, onDrop, onDrag, onLeave, onRemove,
}: {
  books: AttachedBook[];
  extraction: Extraction | null;
  checking: boolean;
  dragging: boolean;
  onFiles: (event: ChangeEvent<HTMLInputElement>) => void;
  onDrop: (event: DragEvent<HTMLElement>) => void;
  onDrag: (event: DragEvent<HTMLElement>) => void;
  onLeave: () => void;
  onRemove: (id: string) => void;
}) {
  const readiness = extraction?.readiness;
  const groups = groupReadiness(readiness);
  const progress = checking ? 18 : readinessProgress(readiness);
  return (
    <section className="rf-readiness rf-stage-enter">
      <div className="rf-stage-title">
        <span className="rf-kicker">Readiness</span>
        <h1>{checking ? "Checking files." : readiness?.ready ? "Ready to analyze." : "More files needed."}</h1>
        <p>{checking ? "Identifying sources." : readiness?.ready ? "Analysis starts automatically." : "Add the missing sources below."}</p>
      </div>
      <div className="rf-readiness-layout">
        <article className="rf-paper-panel">
          <div className="rf-panel-top"><span><small>ATTACHED MATERIAL</small><strong>{books.length} source package{books.length === 1 ? "" : "s"}</strong></span><span className="rf-count">{String(books.length).padStart(2, "0")}</span></div>
          <div className="rf-book-list">
            {books.map((book) => <div className="rf-book" key={book.id}><i><FileIcon name={book.name} /></i><span><strong>{book.name}</strong><small>{formatBytes(book.size)} · received</small></span><em><Check size={11} /> Parsed</em><button aria-label={`Remove ${book.name}`} onClick={() => onRemove(book.id)}><Trash2 size={13} /></button></div>)}
          </div>
          <label className={`rf-compact-drop ${dragging ? "dragging" : ""}`} onDragOver={onDrag} onDragLeave={onLeave} onDrop={onDrop}><Upload size={14} /> Drop more books or <u>browse</u><input hidden multiple type="file" accept={ACCEPTED_BOOKS} onChange={onFiles} /></label>
        </article>
        <article className="rf-paper-panel">
          <div className="rf-panel-top"><span><small>REQUIRED DATA</small><strong>Four source groups</strong></span>{checking ? <LoaderCircle className="rf-spin" size={18} /> : <span className={readiness?.ready ? "rf-chip ready" : "rf-chip"}>{readiness?.ready ? "READY" : "INCOMPLETE"}</span>}</div>
          <div className="rf-readiness-meter"><span><i style={{ width: `${progress}%` }} /></span><strong>{progress}%</strong></div>
          <div className="rf-group-list">
            {groups.map((group, index) => <div className={`rf-source-group ${group.complete ? "complete" : ""}`} key={group.title}><i>{group.complete ? <Check size={13} /> : index + 1}</i><span><strong>{group.title}</strong><small>{group.complete ? `${group.files.length} of ${group.files.length} present` : group.missing.length ? `Missing: ${group.missing.join(", ")}` : "Waiting for classification"}</small></span><em>{group.present}/{group.files.length}</em></div>)}
          </div>
          {!checking && !readiness?.ready && <div className="rf-gate-note"><X size={14} /><span><strong>Analysis locked</strong>All required sources must be present.</span></div>}
        </article>
      </div>
    </section>
  );
}
