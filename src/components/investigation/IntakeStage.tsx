import { ArrowRight, Check, FileArchive, Scale, Upload } from "lucide-react";
import type { ChangeEvent, DragEvent } from "react";
import { ACCEPTED_BOOKS } from "@/lib/investigation";

export function IntakeStage({
  dragging, loadingDemo, onDrag, onLeave, onDrop, onFiles, onDemo,
}: {
  dragging: boolean;
  loadingDemo: boolean;
  onDrag: (event: DragEvent<HTMLElement>) => void;
  onLeave: () => void;
  onDrop: (event: DragEvent<HTMLElement>) => void;
  onFiles: (event: ChangeEvent<HTMLInputElement>) => void;
  onDemo: (scenario: "fraud" | "clean") => void;
}) {
  return (
    <section className="rf-intake rf-stage-enter">
      <div className="rf-intake-copy">
        <span className="rf-kicker">New investigation</span>
        <h1>Follow the money.<br /><em>Prove the finding.</em></h1>
        <p>Upload the ledger, invoices, bank records and supplier data. Findings require a rule, source records and an exact peso amount.</p>
        <div className="rf-principles">
          <span><Scale size={17} /><span><strong>Evidence first</strong><small>An anomaly is not an accusation.</small></span></span>
          <span><Check size={17} /><span><strong>Same process</strong><small>Demo and uploaded cases use the same checks.</small></span></span>
        </div>
      </div>
      <div className="rf-intake-panel">
        <div className="rf-panel-top"><span><small>01 / NEW INVESTIGATION</small><strong>Bring the company books</strong></span><FileArchive size={19} /></div>
        <label className={`rf-dropzone ${dragging ? "dragging" : ""}`} onDragOver={onDrag} onDragLeave={onLeave} onDrop={onDrop}>
          <span className="rf-upload-mark"><Upload size={25} /></span>
          <strong>Drop a ZIP or source files</strong>
          <p>CSV, JSON, PDF and spreadsheets are supported.</p>
          <span className="rf-button rf-button-dark">Choose books <ArrowRight size={13} /></span>
          <input hidden multiple type="file" accept={ACCEPTED_BOOKS} onChange={onFiles} />
        </label>
        <div className="rf-required-note"><Check size={13} /><span>Analysis stays locked until the minimum source set is present.</span></div>
      </div>
      <div className="rf-demo-band">
        <span><FileArchive size={16} /><span><strong>Demo cases</strong><small>Use the full workflow.</small></span></span>
        <div>
          <button className="rf-button rf-button-danger" disabled={loadingDemo} onClick={() => onDemo("fraud")}>Fraud case <ArrowRight size={13} /></button>
          <button className="rf-button rf-button-outline" disabled={loadingDemo} onClick={() => onDemo("clean")}>Clean case</button>
        </div>
      </div>
    </section>
  );
}
