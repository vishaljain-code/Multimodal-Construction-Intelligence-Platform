import React, { useEffect, useState } from "react";
import { FEATURES } from "./features.js";
import { postForm } from "./api.js";
import Result from "./Result.jsx";

function initial(feature) {
  return Object.fromEntries(feature.fields.filter((f) => f.type !== "file").map((f) => [f.name, f.value ?? (f.options?.[0] ?? "")]));
}

function Panel({ feature }) {
  const [values, setValues] = useState(initial(feature));
  const [file, setFile] = useState(null);
  const [state, setState] = useState({ loading: false, data: null, error: "" });

  const submit = async (e) => {
    e.preventDefault();
    setState({ loading: true, data: null, error: "" });
    try {
      const data = await postForm(feature.endpoint, { ...values, file });
      setState({ loading: false, data, error: "" });
    } catch (err) {
      setState({ loading: false, data: null, error: err.message });
    }
  };

  return (
    <section className="panel">
      <h2>{feature.icon} {feature.title}</h2>
      <p className="muted">{feature.blurb}</p>
      <form onSubmit={submit}>
        {feature.fields.map((f) => (
          <label key={f.name}>
            <span>{f.label}{f.required && " *"}</span>
            {f.type === "textarea" ? (
              <textarea rows={3} required={f.required} placeholder={f.placeholder} value={values[f.name]} onChange={(e) => setValues({ ...values, [f.name]: e.target.value })} />
            ) : f.type === "select" ? (
              <select value={values[f.name]} onChange={(e) => setValues({ ...values, [f.name]: e.target.value })}>
                {f.options.map((o) => <option key={o}>{o}</option>)}
              </select>
            ) : f.type === "file" ? (
              <input type="file" accept="image/*" required={f.required} onChange={(e) => setFile(e.target.files[0] || null)} />
            ) : (
              <input type={f.type} required={f.required} placeholder={f.placeholder} value={values[f.name]} onChange={(e) => setValues({ ...values, [f.name]: e.target.value })} />
            )}
          </label>
        ))}
        {file && <img className="preview" src={URL.createObjectURL(file)} alt="preview" />}
        <button disabled={state.loading}>{state.loading ? "Analysing…" : "Analyse"}</button>
      </form>
      {state.error && <div className="error">⚠ {state.error}</div>}
      {state.data && <Result data={state.data} />}
    </section>
  );
}

export default function App() {
  const [active, setActive] = useState(FEATURES[0].id);
  const [health, setHealth] = useState(null);
  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL || ""}/api/health`).then((r) => r.json()).then(setHealth).catch(() => setHealth({ status: "down" }));
  }, []);
  const feature = FEATURES.find((f) => f.id === active);
  return (
    <div className="app">
      <header>
        <h1>🏗️ Construction Intelligence Platform</h1>
        <span className={`dot ${health?.status === "ok" ? "ok" : "bad"}`}>
          {health?.status === "ok" ? (health.llm_configured ? "API online" : "API online · no LLM key") : "API offline"}
        </span>
      </header>
      <nav>
        {FEATURES.map((f) => (
          <button key={f.id} className={f.id === active ? "active" : ""} onClick={() => setActive(f.id)}>{f.icon} {f.title}</button>
        ))}
      </nav>
      <main><Panel key={feature.id} feature={feature} /></main>
    </div>
  );
}
