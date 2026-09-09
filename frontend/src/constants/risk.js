export const RISK_LEVELS = ["Critical", "High", "Medium", "Low"];

export const RISK_CLASS = { Critical: "critical", High: "high", Medium: "med", Low: "low" };

export const RISK_ORDER = Object.fromEntries(RISK_LEVELS.map((level, index) => [level, index]));
