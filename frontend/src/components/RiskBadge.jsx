import { RISK_CLASS } from "../constants/risk";

export default function RiskBadge({ risk }) {
  return <span className={`pill ${RISK_CLASS[risk] || "neutral"}`}>{risk || "Unknown"}</span>;
}
