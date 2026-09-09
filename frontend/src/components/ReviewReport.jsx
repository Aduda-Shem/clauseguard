import { useEffect, useState } from "react";

import { useDownloadReportPdf } from "../api/hooks";
import { RISK_CLASS, RISK_LEVELS, RISK_ORDER } from "../constants/risk";
import { useToast } from "../context/ToastContext.jsx";
import ClauseFindingCard from "./ClauseFindingCard";
import ContractChat from "./ContractChat";
import RiskBadge from "./RiskBadge";

const ACTION_LABELS = {
  APPROVE: "Approve",
  APPROVE_WITH_CONDITIONS: "Approve with conditions",
  NEGOTIATE: "Negotiate before signing",
  ESCALATE: "Escalate to legal",
};

const TABS = [
  { id: "summary", label: "Summary" },
  { id: "clauses", label: "Clauses" },
  { id: "chat", label: "Chat" },
];

export default function ReviewReport({ contract }) {
  const [tab, setTab] = useState("summary");
  const showToast = useToast();
  const downloadReport = useDownloadReportPdf();

  const handleDownload = () => {
    downloadReport.mutate(contract.id, {
      onError: () => showToast("Couldn't generate the PDF report. Try again in a moment.", "error"),
    });
  };

  useEffect(() => {
    setTab("summary");
  }, [contract?.id]);

  if (!contract) {
    return (
      <div className="empty-panel">
        <div className="empty-panel__icon">
          <svg width="40" height="46" viewBox="0 0 24 24" fill="none">
            <path
              d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"
              stroke="#D9CFB8"
              strokeWidth="1.4"
            />
            <path d="M9 12.5h6M9 15.5h6M9 9.5h3" stroke="#D9CFB8" strokeWidth="1.4" strokeLinecap="round" />
          </svg>
        </div>
        <p>Upload or paste a contract to see its risk review here.</p>
      </div>
    );
  }

  if (contract.status === "FAILED") {
    return (
      <div className="error-banner">
        <strong>Review failed.</strong>
        <p>{contract.error_message}</p>
      </div>
    );
  }

  const result = contract.review_result;
  if (!result) {
    return (
      <div className="empty-panel">
        <div className="analyzing-pulse" />
        <p>Reviewing {contract.filename}...</p>
      </div>
    );
  }

  const detected = result.findings
    .filter((f) => !f.is_missing)
    .sort((a, b) => (RISK_ORDER[a.risk_level] ?? 9) - (RISK_ORDER[b.risk_level] ?? 9));
  const missing = result.findings.filter((f) => f.is_missing);

  const counts = Object.fromEntries(RISK_LEVELS.map((level) => [level, 0]));
  for (const f of result.findings) counts[f.risk_level] = (counts[f.risk_level] ?? 0) + 1;
  const totalFindings = result.findings.length || 1;

  return (
    <div className="workspace">
      <div className="workspace-tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={t.id === tab ? "workspace-tab is-active" : "workspace-tab"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "summary" && (
        <div className="workspace-pane">
          <div className="summary-hero">
            <span className="eyebrow">{contract.filename}</span>
            <div className="summary-hero__verdict">
              <RiskBadge risk={result.overall_risk} />
              <span className="verdict-action">{ACTION_LABELS[result.next_action] || result.next_action}</span>
            </div>
            <p className="summary-hero__meta">
              Reviewed in {result.processing_time_ms}ms &middot;{" "}
              {result.engine_mode === "LLM_ENHANCED" ? "Rule-based + LLM redlines" : "Rule-based only"}
            </p>
            <p className="summary-hero__text">{result.summary}</p>
          </div>

          <div className="score-strip">
            {RISK_LEVELS.map((level) => (
              <div key={level} className={`score-chip ${RISK_CLASS[level]}`}>
                <div className="num">{counts[level]}</div>
                <div className="lbl">{level}</div>
              </div>
            ))}
          </div>

          <div className="risk-meter">
            {RISK_LEVELS.map((level) =>
              counts[level] ? (
                <div
                  key={level}
                  className={`risk-meter__segment ${RISK_CLASS[level]}`}
                  style={{ width: `${(counts[level] / totalFindings) * 100}%` }}
                />
              ) : null
            )}
          </div>
          <p className="risk-meter-caption">
            Risk mix across all {totalFindings} categories checked against the playbook.
          </p>

          <div className="summary-actions">
            <button className="btn btn-primary" onClick={() => setTab("clauses")}>
              Review flagged clauses
            </button>
            <button className="btn btn-ghost" onClick={handleDownload} disabled={downloadReport.isPending}>
              {downloadReport.isPending ? "Preparing PDF…" : "Download PDF report"}
            </button>
          </div>
        </div>
      )}

      {tab === "clauses" && (
        <div className="workspace-pane">
          {detected.length > 0 && (
            <>
              <div className="section-label">
                <h4>Flagged clauses</h4>
              </div>
              <div className="findings-list">
                {detected.map((f) => (
                  <ClauseFindingCard key={f.id} finding={f} />
                ))}
              </div>
            </>
          )}

          {missing.length > 0 && (
            <>
              <div className="section-label">
                <h4>Possibly missing</h4>
              </div>
              <div className="findings-list">
                {missing.map((f) => (
                  <ClauseFindingCard key={f.id} finding={f} />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {tab === "chat" && (
        <div className="workspace-pane workspace-pane--chat">
          <ContractChat contract={contract} />
        </div>
      )}
    </div>
  );
}
