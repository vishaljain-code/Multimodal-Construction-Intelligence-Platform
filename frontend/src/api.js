const BASE = import.meta.env.VITE_API_URL || "";

export async function postForm(endpoint, values) {
  const body = new FormData();
  Object.entries(values).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") body.append(k, v);
  });
  const res = await fetch(`${BASE}/api/${endpoint}`, { method: "POST", body });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    throw new Error(typeof d === "string" ? d : "Request failed (" + res.status + ")");
  }
  return data;
}
