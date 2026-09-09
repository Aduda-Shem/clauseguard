import { usePlaybook } from "../api/hooks";

export default function PlaybookView() {
  const playbookQuery = usePlaybook();

  return (
    <div className="playbook-view">
      <div className="summary-hero">
        <span className="eyebrow">The playbook</span>
        <h2 className="hl-heading">
          <span>What ClauseGuard checks for</span>
        </h2>
        <p className="summary-hero__text" style={{ marginTop: 12 }}>
          Every review runs the same {playbookQuery.data?.length ?? "..."} rules below against the
          contract text. Nothing here is hidden -- if a category isn't listed, ClauseGuard doesn't
          check for it yet.
        </p>
      </div>

      {playbookQuery.isLoading && <p className="empty-state">Loading playbook...</p>}

      <div className="def-list">
        {playbookQuery.data?.map((rule) => (
          <div key={rule.key} className="def-row">
            <div className="def-row__head">
              <span className="term">{rule.name}</span>
              <span className="pill neutral">{rule.category}</span>
            </div>
            <p className="short">{rule.missing_reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
