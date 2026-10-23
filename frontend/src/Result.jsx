import React from "react";

const pretty = (k) => k.replace(/_/g, " ");
const BADGES = ["low", "medium", "high", "critical", "good", "caution", "halt", "positive", "neutral", "negative"];

function Value({ v }) {
  if (v === null || v === undefined) return <span className="muted">—</span>;
  if (typeof v === "boolean") return <span>{v ? "Yes" : "No"}</span>;
  if (typeof v === "string" && BADGES.includes(v)) return <span className={`badge b-${v}`}>{v}</span>;
  if (typeof v === "number") return <span>{v.toLocaleString()}</span>;
  if (typeof v === "string") return <span>{v}</span>;
  if (Array.isArray(v)) {
    if (!v.length) return <span className="muted">None</span>;
    if (typeof v[0] !== "object") return <ul>{v.map((x, i) => <li key={i}>{String(x)}</li>)}</ul>;
    return <div className="cards">{v.map((o, i) => <div className="mini" key={i}><Fields obj={o} /></div>)}</div>;
  }
  return <Fields obj={v} />;
}

function Fields({ obj }) {
  return (
    <dl>
      {Object.entries(obj).map(([k, v]) => (
        <React.Fragment key={k}>
          <dt>{pretty(k)}</dt>
          <dd><Value v={v} /></dd>
        </React.Fragment>
      ))}
    </dl>
  );
}

export default function Result({ data }) {
  return (
    <div className="result">
      <Fields obj={data} />
      <details><summary>Raw JSON</summary><pre>{JSON.stringify(data, null, 2)}</pre></details>
    </div>
  );
}
