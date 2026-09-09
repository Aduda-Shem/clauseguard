const THUMB_COLOR = {
  Critical: "#7A2E22",
  High: "#9C4A3A",
  Medium: "#B9832A",
  Low: "#54785A",
};

const ACTION_LABELS = {
  APPROVE: "Approve",
  APPROVE_WITH_CONDITIONS: "Approve with conditions",
  NEGOTIATE: "Negotiate",
  ESCALATE: "Escalate",
};

export default function ContractList({ contracts, selectedId, onSelect, onDelete }) {
  if (!contracts?.length) {
    return <p className="empty-state">No contracts reviewed yet.</p>;
  }

  return (
    <ul className="contract-list">
      {contracts.map((c) => (
        <li key={c.id} className="contract-row-wrap">
          <button
            className={c.id === selectedId ? "contract-row is-selected" : "contract-row"}
            onClick={() => onSelect(c.id)}
          >
            <span className="contract-thumb" style={{ background: THUMB_COLOR[c.overall_risk] || "#8B9089" }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path
                  d="M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"
                  stroke="#fff"
                  strokeWidth="1.6"
                />
              </svg>
            </span>
            <span className="contract-meta">
              <span className="name">{c.filename}</span>
              <span className="sub">
                {c.overall_risk ? `${c.overall_risk} risk` : c.status}
                {c.next_action ? ` · ${ACTION_LABELS[c.next_action] || c.next_action}` : ""}
              </span>
            </span>
          </button>
          <button
            type="button"
            className="contract-delete-btn"
            aria-label={`Delete ${c.filename}`}
            onClick={(e) => {
              e.stopPropagation();
              onDelete(c);
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
              <path
                d="M4 7h16M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3m2 0v13a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V7h10z"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </li>
      ))}
    </ul>
  );
}
