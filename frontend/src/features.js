// Declarative description of every module: drives both the form and the API call.
const t = (name, label, extra = {}) => ({ name, label, type: "text", ...extra });
const area = (name, label, extra = {}) => ({ name, label, type: "textarea", ...extra });
const num = (name, label, extra = {}) => ({ name, label, type: "number", ...extra });
const img = (label, required = false) => ({ name: "file", label, type: "file", required });

export const FEATURES = [
  { id: "safety", icon: "🦺", title: "Site Safety", endpoint: "safety",
    blurb: "Upload a site photo to detect PPE and hazard violations.",
    fields: [img("Site image"), area("notes", "Site notes (optional)")] },
  { id: "cracks", icon: "🧱", title: "Crack Detection", endpoint: "cracks",
    blurb: "Classify cracks and get severity, causes and actions.",
    fields: [img("Wall / slab / column image", true), t("location", "Location (e.g. ground floor wall)"), area("notes", "Notes")] },
  { id: "valuation", icon: "🏠", title: "Real Estate Valuation", endpoint: "valuation",
    blurb: "Estimate a property's market value range.",
    fields: [t("location", "Location", { required: true, placeholder: "Indore, Madhya Pradesh" }),
      { name: "property_type", label: "Type", type: "select", options: ["residential", "commercial", "plot", "villa", "apartment"] },
      num("area_sqft", "Area (sq ft)", { required: true, value: 1200 }), num("age_years", "Age (years)", { value: 0 }),
      { name: "condition", label: "Condition", type: "select", options: ["excellent", "good", "average", "poor"], value: "good" },
      t("currency", "Currency", { value: "INR" }), area("notes", "Notes"), img("Property photo (optional)")] },
  { id: "planning", icon: "📐", title: "Project Planning", endpoint: "planning",
    blurb: "Generate phased schedule, materials, risks and cost range.",
    fields: [t("project_type", "Project type", { required: true, placeholder: "G+1 residential house" }), t("location", "Location"),
      num("area_sqft", "Built-up area (sq ft)", { required: true, value: 1500 }), num("floors", "Floors", { value: 2 }),
      t("budget", "Budget (optional)"), area("notes", "Notes")] },
  { id: "assistant", icon: "🧑‍🔧", title: "Daily Site Assistant", endpoint: "assistant",
    blurb: "Describe today's situation; get prioritised actions.",
    fields: [area("message", "Message", { required: true, placeholder: "Slab pour is tomorrow, 2 masons absent..." }), img("Photo (optional)")] },
  { id: "weather", icon: "🌦️", title: "Weather Advisory", endpoint: "weather",
    blurb: "Live forecast turned into work-suitability advice.",
    fields: [t("city", "City", { required: true, placeholder: "Bhopal" }), t("activity", "Planned activity", { placeholder: "Concrete pouring" })] },
  { id: "knowledge", icon: "📚", title: "Knowledge Assistant", endpoint: "knowledge",
    blurb: "Ask about materials, methods, codes and standards.",
    fields: [area("question", "Question", { required: true, placeholder: "Curing period for M25 concrete?" })] },
];
