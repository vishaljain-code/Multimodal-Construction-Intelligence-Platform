import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import TypeVar

import httpx
import streamlit as st
from anthropic import Anthropic
from pydantic import BaseModel, ValidationError

# Add backend directory to sys.path to import project modules
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from app import prompts, schemas
except ImportError:
    # Fallback to local import if backend dir structure varies
    import prompts  # type: ignore
    import schemas  # type: ignore

T = TypeVar("T", bound=BaseModel)

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Multimodal Construction Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished construction UI styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .badge-card {
        padding: 1rem;
        border-radius: 8px;
        background-color: #1e293b;
        border: 1px solid #334155;
        margin-bottom: 1rem;
    }
    .badge-critical { color: #ef4444; font-weight: bold; }
    .badge-high { color: #f97316; font-weight: bold; }
    .badge-medium { color: #eab308; font-weight: bold; }
    .badge-low { color: #22c55e; font-weight: bold; }
    .badge-good { color: #22c55e; font-weight: bold; }
    .badge-caution { color: #eab308; font-weight: bold; }
    .badge-halt { color: #ef4444; font-weight: bold; }
    .stAlert { margin-top: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- API Key & Client Helper ---
def get_api_key() -> str:
    """Retrieve Anthropic API key from sidebar, Streamlit secrets, or environment."""
    key = st.session_state.get("user_api_key", "").strip()
    if key:
        return key
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return str(st.secrets["ANTHROPIC_API_KEY"]).strip()
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def extract_json_payload(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM output.")
    return json.loads(text[start : end + 1])


def run_claude_json(
    system_prompt: str,
    user_prompt: str,
    schema_cls: type[T],
    image_data: tuple[str, bytes] | None = None,
    api_key: str = "",
    model_name: str = "claude-3-5-sonnet-20241022",
) -> T:
    if not api_key:
        raise ValueError(
            "Anthropic API key is not set. Please provide it in the sidebar or via Streamlit Secrets (ANTHROPIC_API_KEY)."
        )

    client = Anthropic(api_key=api_key)
    content: list[dict] = []

    if image_data:
        mime, raw_bytes = image_data
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime,
                    "data": base64.b64encode(raw_bytes).decode("utf-8"),
                },
            }
        )

    schema_json = json.dumps(schema_cls.model_json_schema())
    content.append(
        {
            "type": "text",
            "text": (
                f"{user_prompt}\n\n"
                f"Respond with ONLY a valid JSON object (no markdown, no preamble) conforming to this JSON Schema:\n"
                f"{schema_json}"
            ),
        }
    )

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            resp = client.messages.create(
                model=model_name,
                max_tokens=3500,
                system=system_prompt,
                messages=[{"role": "user", "content": content}],
            )
            raw_text = "".join(b.text for b in resp.content if b.type == "text")
            parsed = extract_json_payload(raw_text)
            return schema_cls.model_validate(parsed)
        except (ValueError, ValidationError) as e:
            last_error = e

    raise RuntimeError(f"Failed to generate structured JSON after retry: {last_error}")


# --- Sidebar Setup ---
with st.sidebar:
    st.title("🏗️ Platform Controls")
    st.markdown("Decision support intelligence for construction professionals.")

    # Secret / Env key check
    current_key = get_api_key()
    has_preconfigured_key = bool(current_key)

    if has_preconfigured_key:
        st.success("🔑 Anthropic API Key is active")
        with st.expander("Override API Key"):
            custom_key = st.text_input(
                "Enter custom Anthropic API key",
                type="password",
                help="Leave empty to use pre-configured key",
                key="custom_api_key_input",
            )
            if custom_key:
                st.session_state["user_api_key"] = custom_key
    else:
        st.warning("⚠️ No Anthropic API Key detected")
        key_input = st.text_input(
            "Enter Anthropic API Key:",
            type="password",
            help="Your key is kept only in this browser session.",
            key="user_api_key_input",
        )
        if key_input:
            st.session_state["user_api_key"] = key_input
            st.rerun()

    model_choice = st.selectbox(
        "Anthropic Model",
        options=[
            "claude-3-5-sonnet-20241022",
            "claude-3-7-sonnet-20250219",
            "claude-3-5-haiku-20241022",
        ],
        index=0,
        help="Select model version for multimodal reasoning.",
    )

    st.markdown("---")
    st.markdown("### Modules")
    selected_module = st.radio(
        "Select Feature",
        options=[
            "🦺 Site Safety Inspection",
            "🧱 Crack Detection & Diagnosis",
            "🏠 Real Estate Valuation",
            "📐 Project Planning & Scheduling",
            "🧑‍🔧 Daily Site Assistant",
            "🌦️ Weather Advisory",
            "📚 Codes & Knowledge Assistant",
        ],
    )

    st.markdown("---")
    st.markdown(
        "<small>⚠️ <b>Disclaimer:</b> All outputs are AI-generated aids. Engineering decisions, safety audits, and property valuations must be validated by certified professionals.</small>",
        unsafe_allow_html=True,
    )


# Helper function to get image tuple from uploaded file
def process_uploaded_image(uploaded_file):
    if uploaded_file is None:
        return None
    bytes_data = uploaded_file.getvalue()
    content_type = uploaded_file.type or "image/jpeg"
    return (content_type, bytes_data)


# Helper for rendering raw json & download button
def render_json_export(data_obj: BaseModel, file_prefix: str):
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        with st.expander("🔍 View Raw Validated JSON"):
            json_str = data_obj.model_dump_json(indent=2)
            st.code(json_str, language="json")
    with col2:
        st.download_button(
            label="📥 Download JSON",
            data=data_obj.model_dump_json(indent=2),
            file_name=f"{file_prefix}_report.json",
            mime="application/json",
            use_container_width=True,
        )


# ==========================================
# MODULE 1: SITE SAFETY INSPECTION
# ==========================================
if selected_module == "🦺 Site Safety Inspection":
    st.markdown('<div class="main-header">🦺 Construction Site Safety Inspection</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload site photos to inspect PPE compliance, fall hazards, scaffolding, and safety protocol breaches.</div>', unsafe_allow_html=True)

    col_input, col_preview = st.columns([1, 1])
    with col_input:
        site_img = st.file_uploader("Upload Site Photograph (JPEG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"], key="safety_img")
        site_notes = st.text_area("Site Notes / Context (optional)", placeholder="e.g. 5th floor slab casting work, 12 workers present.", key="safety_notes")
        run_btn = st.button("Run Safety Analysis", type="primary", use_container_width=True)

    with col_preview:
        if site_img:
            st.image(site_img, caption="Site Inspection Image", use_container_width=True)
        else:
            st.info("📷 Upload an image on the left to inspect visual hazards.")

    if run_btn:
        active_key = get_api_key()
        if not active_key:
            st.error("Please provide your Anthropic API Key in the sidebar to proceed.")
        elif not site_img and not site_notes.strip():
            st.warning("Please provide either a site photograph or site observations.")
        else:
            img_payload = process_uploaded_image(site_img)
            with st.spinner("Analyzing site safety protocols with multimodal vision..."):
                try:
                    result: schemas.SafetyReport = run_claude_json(
                        system_prompt=prompts.SAFETY,
                        user_prompt=f"Site notes: {site_notes or 'none'}",
                        schema_cls=schemas.SafetyReport,
                        image_data=img_payload,
                        api_key=active_key,
                        model_name=model_choice,
                    )

                    st.success("Safety inspection report generated!")
                    m1, m2 = st.columns([1, 1])
                    with m1:
                        st.metric("Safety Score", f"{result.safety_score} / 100")
                    with m2:
                        risk_color = {"low": "🟢 LOW", "medium": "🟡 MEDIUM", "high": "🟠 HIGH", "critical": "🔴 CRITICAL"}.get(result.overall_risk, result.overall_risk.upper())
                        st.metric("Overall Risk Level", risk_color)

                    st.markdown("### Executive Summary")
                    st.write(result.summary)

                    st.markdown("### 🦺 PPE Compliance")
                    st.info(result.ppe_summary)

                    st.markdown("### 🚨 Detected Violations & Corrective Actions")
                    if not result.violations:
                        st.success("No critical violations detected. Standard precautions apply.")
                    else:
                        for idx, v in enumerate(result.violations, 1):
                            with st.container():
                                st.markdown(
                                    f"""
                                    <div class="badge-card">
                                        <b>#{idx} {v.issue}</b> — <span class="badge-{v.severity}">{v.severity.upper()}</span><br>
                                        <small>📍 <b>Location:</b> {v.location or 'General site area'}</small><br>
                                        🛠️ <b>Action Required:</b> {v.recommendation}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                    render_json_export(result, "safety")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")


# ==========================================
# MODULE 2: CRACK DETECTION & DIAGNOSIS
# ==========================================
elif selected_module == "🧱 Crack Detection & Diagnosis":
    st.markdown('<div class="main-header">🧱 Structural Crack Detection & Diagnosis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Classify wall, slab, or column cracks to estimate severity, structural causes, and repair actions.</div>', unsafe_allow_html=True)

    col_input, col_preview = st.columns([1, 1])
    with col_input:
        crack_img = st.file_uploader("Upload Structural Element Photo (Required)", type=["jpg", "jpeg", "png", "webp"], key="crack_img")
        crack_loc = st.text_input("Surface / Location", placeholder="e.g. Ground floor shear wall near window corner", key="crack_loc")
        crack_notes = st.text_area("Observed Notes", placeholder="e.g. Appeared after recent heavy monsoon rainfall.", key="crack_notes")
        run_btn = st.button("Diagnose Crack", type="primary", use_container_width=True)

    with col_preview:
        if crack_img:
            st.image(crack_img, caption="Structural Surface Photo", use_container_width=True)
        else:
            st.info("📷 Please upload an image of the cracked surface to start the diagnosis.")

    if run_btn:
        active_key = get_api_key()
        if not active_key:
            st.error("Please provide your Anthropic API Key in the sidebar.")
        elif not crack_img:
            st.warning("An image file is required for crack classification.")
        else:
            img_payload = process_uploaded_image(crack_img)
            with st.spinner("Classifying crack pattern and structural risk..."):
                try:
                    result: schemas.CrackReport = run_claude_json(
                        system_prompt=prompts.CRACK,
                        user_prompt=f"Surface/location: {crack_loc or 'unknown'}\nNotes: {crack_notes or 'none'}",
                        schema_cls=schemas.CrackReport,
                        image_data=img_payload,
                        api_key=active_key,
                        model_name=model_choice,
                    )

                    st.success("Crack diagnostic report completed!")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Crack Detected", "Yes" if result.crack_detected else "No")
                    with c2:
                        st.metric("Severity", result.severity.upper())
                    with c3:
                        st.metric("Urgency", result.urgency.title())

                    st.markdown(f"**Crack Classification:** `{result.crack_type}`")
                    if result.estimated_width_mm:
                        st.markdown(f"**Estimated Width:** `{result.estimated_width_mm} mm` (Confidence: {int(result.confidence * 100)}%)")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("#### 🔬 Probable Causes")
                        for cause in result.probable_causes:
                            st.markdown(f"- {cause}")

                    with col_b:
                        st.markdown("#### 🛠️ Recommended Actions")
                        for act in result.recommended_actions:
                            st.markdown(f"- {act}")

                    st.warning(f"⚠️ **Engineering Disclaimer:** {result.disclaimer}")
                    render_json_export(result, "crack")
                except Exception as e:
                    st.error(f"Diagnosis failed: {e}")


# ==========================================
# MODULE 3: REAL ESTATE VALUATION
# ==========================================
elif selected_module == "🏠 Real Estate Valuation":
    st.markdown('<div class="main-header">🏠 Real Estate & Property Valuation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Estimate property market valuation ranges based on structural parameters, location, and photos.</div>', unsafe_allow_html=True)

    with st.form("valuation_form"):
        r1, r2, r3 = st.columns(3)
        with r1:
            loc = st.text_input("Property Location *", value="Indore, Madhya Pradesh", help="City, locality or address")
            prop_type = st.selectbox("Property Type", options=["residential", "commercial", "plot", "villa", "apartment"])
        with r2:
            area_sqft = st.number_input("Built-up / Plot Area (sq ft) *", min_value=50.0, value=1200.0, step=50.0)
            age_years = st.number_input("Property Age (years)", min_value=0, value=2, step=1)
        with r3:
            condition = st.selectbox("Condition", options=["excellent", "good", "average", "poor"], index=1)
            currency = st.text_input("Currency", value="INR")

        prop_notes = st.text_area("Additional Notes (e.g. proximity to metro, corner plot, road width)", value="")
        prop_img = st.file_uploader("Upload Property Photo (Optional)", type=["jpg", "jpeg", "png", "webp"])
        submit_val = st.form_submit_button("Estimate Valuation", type="primary", use_container_width=True)

    if submit_val:
        active_key = get_api_key()
        if not active_key:
            st.error("Please provide your Anthropic API Key in the sidebar.")
        elif not loc.strip():
            st.warning("Please specify the property location.")
        else:
            img_payload = process_uploaded_image(prop_img)
            prompt = (
                f"Location: {loc}\nType: {prop_type}\nArea: {area_sqft} sq ft\n"
                f"Age: {age_years} years\nCondition: {condition}\nCurrency: {currency}\n"
                f"Notes: {prop_notes or 'none'}"
            )
            with st.spinner("Computing valuation model and market trend benchmarks..."):
                try:
                    result: schemas.ValuationReport = run_claude_json(
                        system_prompt=prompts.VALUATION,
                        user_prompt=prompt,
                        schema_cls=schemas.ValuationReport,
                        image_data=img_payload,
                        api_key=active_key,
                        model_name=model_choice,
                    )

                    st.success("Valuation benchmark ready!")
                    v1, v2, v3 = st.columns(3)
                    with v1:
                        st.metric("Estimated Value Range", f"{result.currency} {result.estimated_value_low:,.0f} – {result.estimated_value_high:,.0f}")
                    with v2:
                        st.metric("Price / Sq.Ft", f"{result.currency} {result.price_per_sqft:,.2f}")
                    with v3:
                        st.metric("Confidence Level", f"{int(result.confidence * 100)}%")

                    st.markdown("### Market Outlook")
                    st.write(result.market_outlook)

                    st.markdown("### Valuation Factors")
                    for f in result.factors:
                        badge = {"positive": "🟢 POSITIVE", "negative": "🔴 NEGATIVE", "neutral": "⚪ NEUTRAL"}.get(f.impact, f.impact.upper())
                        st.markdown(f"- **{f.factor}** ({badge}): {f.note}")

                    if result.assumptions:
                        with st.expander("Key Assumptions Made"):
                            for a in result.assumptions:
                                st.markdown(f"- {a}")

                    render_json_export(result, "valuation")
                except Exception as e:
                    st.error(f"Valuation failed: {e}")


# ==========================================
# MODULE 4: PROJECT PLANNING & SCHEDULING
# ==========================================
elif selected_module == "📐 Project Planning & Scheduling":
    st.markdown('<div class="main-header">📐 Phased Construction Project Planner</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Generate realistic construction milestones, duration schedules, material requirements, and risk matrix.</div>', unsafe_allow_html=True)

    with st.form("planning_form"):
        c1, c2 = st.columns(2)
        with c1:
            project_type = st.text_input("Project Type *", value="G+2 Residential Building", placeholder="e.g. Commercial Office, G+1 Villa")
            area = st.number_input("Total Built-up Area (sq ft) *", min_value=100.0, value=2500.0, step=100.0)
            floors = st.number_input("Number of Floors", min_value=1, value=3, step=1)
        with c2:
            location = st.text_input("Project Location", value="Bengaluru, Karnataka")
            budget = st.text_input("Target Budget / Constraints", value="INR 75 Lakhs")
            notes = st.text_area("Specific Requirements / Constraints", placeholder="e.g. Red brick masonry preferred, completion before monsoon.")

        plan_btn = st.form_submit_button("Generate Project Plan", type="primary", use_container_width=True)

    if plan_btn:
        active_key = get_api_key()
        if not active_key:
            st.error("Please provide your Anthropic API Key in the sidebar.")
        else:
            prompt = (
                f"Project: {project_type}\nLocation: {location or 'unspecified'}\n"
                f"Built-up area: {area} sq ft\nFloors: {floors}\n"
                f"Budget: {budget or 'unspecified'}\nNotes: {notes or 'none'}"
            )
            with st.spinner("Synthesizing structural milestones, procurement lead times, and scheduling..."):
                try:
                    result: schemas.PlanReport = run_claude_json(
                        system_prompt=prompts.PLANNING,
                        user_prompt=prompt,
                        schema_cls=schemas.PlanReport,
                        api_key=active_key,
                        model_name=model_choice,
                    )

                    st.success("Construction schedule synthesized!")
                    p1, p2 = st.columns(2)
                    with p1:
                        st.metric("Total Estimated Duration", f"{result.total_duration_days} days (~{result.total_duration_days // 30} months)")
                    with p2:
                        st.metric("Estimated Cost Range", result.estimated_cost_range)

                    st.markdown("### 📅 Phased Execution Breakdown")
                    for i, phase in enumerate(result.phases, 1):
                        with st.expander(f"Phase {i}: {phase.name} ({phase.duration_days} Days)", expanded=(i == 1)):
                            st.markdown(f"**Key Tasks:** {', '.join(phase.tasks)}")
                            st.markdown(f"**Required Materials:** {', '.join(phase.materials)}")
                            if phase.risks:
                                st.markdown(f"**Key Risks & Mitigation:** {', '.join(phase.risks)}")

                    col_cp, col_rn = st.columns(2)
                    with col_cp:
                        st.markdown("#### ⚡ Critical Path Activities")
                        for item in result.critical_path:
                            st.markdown(f"- ⚠️ {item}")

                    with col_rn:
                        st.markdown("#### 📦 Resource & Machinery Needs")
                        for item in result.resource_needs:
                            st.markdown(f"- 🚜 {item}")

                    if result.recommendations:
                        st.markdown("#### 💡 Expert Recommendations")
                        for rec in result.recommendations:
                            st.markdown(f"- {rec}")

                    render_json_export(result, "project_plan")
                except Exception as e:
                    st.error(f"Planning failed: {e}")


# ==========================================
# MODULE 5: DAILY SITE ASSISTANT
# ==========================================
elif selected_module == "🧑‍🔧 Daily Site Assistant":
    st.markdown('<div class="main-header">🧑‍🔧 Daily Site Assistant & Problem Solver</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Describe site blockers, labor shortages, pouring schedules, or upload site issues for immediate resolution.</div>', unsafe_allow_html=True)

    col_in, col_up = st.columns([1, 1])
    with col_in:
        site_msg = st.text_area(
            "Site Update / Challenge *",
            placeholder="e.g. Slab pour is scheduled for 10 AM tomorrow, but 3 masons are absent and the bar bending audit found inadequate cover on the cantilever beam. What are our immediate actions?",
            height=160,
        )
        assist_img = st.file_uploader("Attach Photo (Optional)", type=["jpg", "jpeg", "png", "webp"])
        ask_assist = st.button("Get Actionable Advice", type="primary", use_container_width=True)

    with col_up:
        if assist_img:
            st.image(assist_img, caption="Attached Site Image", use_container_width=True)
        else:
            st.info("💡 You can attach a photo of the defect, reinforcement, formwork, or drawings for multimodal analysis.")

    if ask_assist:
        active_key = get_api_key()
        if not active_key:
            st.error("Please provide your Anthropic API Key in the sidebar.")
        elif not site_msg.strip():
            st.warning("Please describe your site situation.")
        else:
            img_payload = process_uploaded_image(assist_img)
            with st.spinner("Analyzing site scenario and generating priority mitigation protocol..."):
                try:
                    result: schemas.AssistantReport = run_claude_json(
                        system_prompt=prompts.ASSISTANT,
                        user_prompt=site_msg,
                        schema_cls=schemas.AssistantReport,
                        image_data=img_payload,
                        api_key=active_key,
                        model_name=model_choice,
                    )

                    pri_color = {"low": "🟢 LOW", "medium": "🟡 MEDIUM", "high": "🟠 HIGH", "critical": "🔴 CRITICAL"}.get(result.priority, result.priority.upper())
                    st.metric("Action Priority", pri_color)

                    st.markdown("### Guidance & Strategy")
                    st.write(result.answer)

                    st.markdown("### ✅ Immediate Action Items")
                    for idx, item in enumerate(result.action_items, 1):
                        st.checkbox(f"**Step {idx}:** {item}", key=f"action_chk_{idx}")

                    if result.follow_up_questions:
                        with st.expander("❓ Questions to Verify on Site"):
                            for q in result.follow_up_questions:
                                st.markdown(f"- {q}")

                    render_json_export(result, "site_assistant")
                except Exception as e:
                    st.error(f"Assistant query failed: {e}")


# ==========================================
# MODULE 6: WEATHER ADVISORY
# ==========================================
elif selected_module == "🌦️ Weather Advisory":
    st.markdown('<div class="main-header">🌦️ Construction Weather Advisory</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Live weather telemetry (via Open-Meteo) translated into concrete pouring, crane operation, and site safety advice.</div>', unsafe_allow_html=True)

    w1, w2 = st.columns([1, 1])
    with w1:
        city = st.text_input("City / Project Location *", value="Bhopal", placeholder="e.g. Mumbai, Dubai, London")
    with w2:
        activity = st.text_input("Planned Activity", value="Concrete slab casting", placeholder="e.g. Tower crane lifting, Excavation, Painting")

    check_wx = st.button("Check Weather & Work Feasibility", type="primary", use_container_width=True)

    if check_wx:
        active_key = get_api_key()
        if not active_key:
            st.error("Please provide your Anthropic API Key in the sidebar.")
        elif not city.strip():
            st.warning("Please specify a city name.")
        else:
            with st.spinner(f"Fetching live meteorology data for {city}..."):
                try:
                    with httpx.Client(timeout=10) as client:
                        geo_resp = client.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1})
                        geo_data = geo_resp.json()
                        if not geo_data.get("results"):
                            st.error(f"Could not locate city '{city}'. Please verify spelling.")
                            st.stop()

                        loc_info = geo_data["results"][0]
                        lat, lon = loc_info["latitude"], loc_info["longitude"]

                        wx_resp = client.get(
                            "https://api.open-meteo.com/v1/forecast",
                            params={
                                "latitude": lat,
                                "longitude": lon,
                                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                                "daily": "precipitation_sum,temperature_2m_max,wind_speed_10m_max",
                                "forecast_days": 3,
                            },
                        )
                        wx_data = wx_resp.json()

                    curr = wx_data.get("current", {})
                    st.info(f"📍 **Location:** {loc_info.get('name')}, {loc_info.get('admin1', '')} {loc_info.get('country', '')} (Lat: {lat:.2f}, Lon: {lon:.2f})")

                    t1, t2, t3, t4 = st.columns(4)
                    with t1:
                        st.metric("Temperature", f"{curr.get('temperature_2m', 'N/A')} °C")
                    with t2:
                        st.metric("Humidity", f"{curr.get('relative_humidity_2m', 'N/A')} %")
                    with t3:
                        st.metric("Wind Speed", f"{curr.get('wind_speed_10m', 'N/A')} km/h")
                    with t4:
                        st.metric("Precipitation", f"{curr.get('precipitation', 'N/A')} mm")

                    prompt = f"City: {loc_info['name']}, {loc_info.get('country', '')}\nPlanned activity: {activity or 'general'}\nWeather JSON: {wx_data}"

                    with st.spinner("Synthesizing engineering weather advisory..."):
                        result: schemas.WeatherAdvisory = run_claude_json(
                            system_prompt=prompts.WEATHER,
                            user_prompt=prompt,
                            schema_cls=schemas.WeatherAdvisory,
                            api_key=active_key,
                            model_name=model_choice,
                        )

                        suit_badge = {
                            "good": "🟢 GOOD (Safe to Proceed)",
                            "caution": "🟡 CAUTION (Apply Precautions)",
                            "halt": "🔴 HALT (Unsafe for Outdoor Work)",
                        }.get(result.work_suitability, result.work_suitability.upper())

                        st.metric("Work Feasibility", suit_badge)
                        st.markdown("### Meteorological Assessment")
                        st.write(result.summary)

                        col_ok, col_no = st.columns(2)
                        with col_ok:
                            st.markdown("#### ✅ Safe / Recommended Activities")
                            for a in result.recommended_activities:
                                st.markdown(f"- {a}")

                        with col_no:
                            st.markdown("#### ⛔ Activities to Avoid / Reschedule")
                            for a in result.avoid_activities:
                                st.markdown(f"- {a}")

                        if result.precautions:
                            st.markdown("#### 🛡️ Required Safety Precautions")
                            for p in result.precautions:
                                st.markdown(f"- {p}")

                        render_json_export(result, "weather_advisory")

                except httpx.HTTPError as he:
                    st.error(f"Weather service unavailable: {he}")
                except Exception as e:
                    st.error(f"Advisory generation failed: {e}")


# ==========================================
# MODULE 7: CODES & KNOWLEDGE ASSISTANT
# ==========================================
elif selected_module == "📚 Codes & Knowledge Assistant":
    st.markdown('<div class="main-header">📚 Construction Codes & Knowledge Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask technical questions regarding building codes (IS, ACI, Eurocodes), materials, curing times, and QA standards.</div>', unsafe_allow_html=True)

    preset_questions = [
        "Select an example question or type below...",
        "What is the minimum curing period for M25 concrete with OPC cement as per IS 456:2000?",
        "What is the maximum permissible deflection for an RCC cantilever beam according to ACI 318?",
        "What are the standard slump values recommended for pumped concrete?",
        "What is the lap length required for 20mm Fe500 rebars in tension?",
    ]

    selected_preset = st.selectbox("Example Technical Queries", options=preset_questions)
    default_text = "" if selected_preset == preset_questions[0] else selected_preset

    query = st.text_area("Your Construction Engineering Question *", value=default_text, placeholder="e.g. What is the minimum stripping time for slab soffit formwork spans up to 4.5m?", height=120)
    ask_btn = st.button("Consult Knowledge Assistant", type="primary", use_container_width=True)

    if ask_btn:
        active_key = get_api_key()
        if not active_key:
            st.error("Please provide your Anthropic API Key in the sidebar.")
        elif not query.strip():
            st.warning("Please type your question.")
        else:
            with st.spinner("Querying engineering standards and code references..."):
                try:
                    result: schemas.KnowledgeReport = run_claude_json(
                        system_prompt=prompts.KNOWLEDGE,
                        user_prompt=query,
                        schema_cls=schemas.KnowledgeReport,
                        api_key=active_key,
                        model_name=model_choice,
                    )

                    st.markdown("### Technical Answer")
                    st.write(result.answer)

                    k1, k2 = st.columns(2)
                    with k1:
                        st.markdown("#### 📌 Key Points")
                        for kp in result.key_points:
                            st.markdown(f"- {kp}")

                    with k2:
                        st.markdown("#### 📖 Standards & Codes Referenced")
                        if not result.standards_referenced:
                            st.markdown("- *General structural engineering principles*")
                        else:
                            for std in result.standards_referenced:
                                st.markdown(f"- 🏷️ **{std}**")

                    if result.related_topics:
                        with st.expander("🔗 Related Engineering Topics"):
                            for topic in result.related_topics:
                                st.markdown(f"- {topic}")

                    render_json_export(result, "knowledge")
                except Exception as e:
                    st.error(f"Query failed: {e}")
