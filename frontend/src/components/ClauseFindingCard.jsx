import RiskBadge from "./RiskBadge";

export default function ClauseFindingCard({ finding }) {
  if (finding.is_missing) {
    return (
      <div className="card missing-card">
        <p>
          <strong>{finding.category}</strong> -- {finding.reason}
        </p>
      </div>
    );
  }

  return (
    <div className="card risk-card">
      <div className="head">
        <h5>{finding.category}</h5>
        <RiskBadge risk={finding.risk_level} />
      </div>
      <p className="why">{finding.reason}</p>
      <blockquote className="excerpt">&ldquo;...{finding.matched_text}...&rdquo;</blockquote>
      {finding.redline_suggestion && (
        <div className="redline">
          <span className="eyebrow">Suggested next step</span>
          {finding.redline_suggestion}
        </div>
      )}
    </div>
  );
}
