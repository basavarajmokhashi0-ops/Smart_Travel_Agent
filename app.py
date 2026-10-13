"""
app.py  —  Smart Travel Planner
Streamlit UI | CrewAI + MCP Tools | Gemini 2.5 Flash

THREADING RULE:
  Background thread (crew_worker) — pure computation, zero Streamlit calls.
  Main thread — owns all st.* / placeholder.* calls.
  Communication via plain Python dicts: result_box, error_box.
"""

import streamlit as st
import os
import sys
import threading
import time
from datetime import date, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

st.set_page_config(
    page_title="Smart Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stp-header {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    padding: 2.2rem 2rem 1.8rem;
    border-radius: 16px;
    color: white;
    text-align: center;
    margin-bottom: 1.8rem;
    box-shadow: 0 8px 32px rgba(15,52,96,0.4);
}
.stp-header h1 { margin:0; font-size:2.4rem; letter-spacing:-0.5px; }
.stp-header p  { margin:0.4rem 0 0; opacity:0.75; font-size:1rem; }
.stp-header .badge {
    display:inline-block; background:rgba(255,255,255,0.12);
    border:1px solid rgba(255,255,255,0.2); border-radius:20px;
    padding:0.2rem 0.8rem; font-size:0.78rem; margin:0.6rem 0.2rem 0;
}
.agent-card {
    background:#f0f4ff; border-left:3px solid #2c5364;
    padding:0.6rem 0.9rem; border-radius:0 6px 6px 0;
    margin:0.5rem 0; font-size:0.85rem;
}
.agent-card strong { color:#2c5364; display:block; margin-bottom:2px; }
.tool-tag {
    display:inline-block; background:#e8f8f0; border:1px solid #9be0bf;
    color:#1a6e45; border-radius:4px; padding:1px 5px;
    font-size:0.68rem; font-weight:600; margin-left:3px; vertical-align:middle;
}
.status-running {
    background:#fffbeb; border:1px solid #f59e0b; border-radius:10px;
    padding:1rem 1.2rem; color:#92400e; margin:1rem 0;
}
.status-done {
    background:#ecfdf5; border:1px solid #10b981; border-radius:10px;
    padding:1rem 1.2rem; color:#065f46; margin:1rem 0;
}
.status-error {
    background:#fef2f2; border:1px solid #f87171; border-radius:10px;
    padding:1rem 1.2rem; color:#7f1d1d; margin:1rem 0;
}
.info-box {
    background:#f0f4ff; border:1px solid #c7d2fe; border-radius:8px;
    padding:0.7rem 1rem; font-size:0.85rem; color:#3730a3; margin:0.5rem 0;
}
#MainMenu, footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="stp-header">
    <h1>✈️ Smart Travel Planner</h1>
    <p>Autonomous multi-agent AI — real MCP tool calls at runtime</p>
    <span class="badge">🤖 CrewAI</span>
    <span class="badge">🔧 MCP Tools</span>
    <span class="badge">💎 Gemini 2.5 Flash</span>
    <span class="badge">5 Specialized Agents</span>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    with st.expander("🔑 API Keys", expanded=True):
        gemini_input = st.text_input(
            "Gemini API Key ✅ Required",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            placeholder="AIza...",
            help="Free at aistudio.google.com",
        )
        if gemini_input.strip():
            os.environ["GEMINI_API_KEY"] = gemini_input.strip()
            # LiteLLM reads GEMINI_API_KEY automatically
            os.environ["GOOGLE_API_KEY"] = gemini_input.strip()

        if os.getenv("GEMINI_API_KEY"):
            st.success("✅ Gemini key loaded")
        else:
            st.warning("⚠️ Enter your Gemini API key")
            st.markdown("[Get free key →](https://aistudio.google.com)")

        st.markdown("---")

        serper_input = st.text_input(
            "Serper API Key (recommended)",
            type="password",
            value=os.getenv("SERPER_API_KEY", ""),
            placeholder="Leave blank — agents still work",
            help="For live Google search results. Free 2500/month at serper.dev",
        )
        if serper_input.strip():
            os.environ["SERPER_API_KEY"] = serper_input.strip()

        owm_input = st.text_input(
            "OpenWeatherMap Key (optional)",
            type="password",
            value=os.getenv("OPENWEATHER_API_KEY", ""),
            placeholder="Leave blank — uses estimates",
            help="For live weather. Free at openweathermap.org/api",
        )
        if owm_input.strip():
            os.environ["OPENWEATHER_API_KEY"] = owm_input.strip()

        c1, c2 = st.columns(2)
        with c1:
            st.success("🔍 Live search") if os.getenv("SERPER_API_KEY") else st.info("🔍 DDG/LLM")
        with c2:
            st.success("🌤️ Live weather") if os.getenv("OPENWEATHER_API_KEY") else st.info("🌤️ Estimated")

    st.markdown("---")
    st.markdown("### 🤖 Agent Pipeline")

    agents_info = [
        ("🧠", "Planner",   "Route analysis + execution plan",         ["📅 date", "🔍 search"]),
        ("✈️", "Travel",    "Flights / trains / buses — 3 options",    ["🔍 search"]),
        ("🏨", "Hotel",     "3 hotels across 3 areas",                 ["🔍 search"]),
        ("📍", "Info",      "Weather, food, attractions, tips",        ["🔍 search", "🌤️ weather"]),
        ("📅", "Itinerary", "Day-by-day plan + budget summary",        ["🔍 search"]),
    ]
    for icon, name, desc, tools in agents_info:
        tool_tags = "".join(f'<span class="tool-tag">{t}</span>' for t in tools)
        st.markdown(f"""
        <div class="agent-card">
            <strong>{icon} {name} {tool_tags}</strong>
            {desc}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔧 MCP Tools")
    st.markdown("""
- 📅 **get_current_date** — real date/time
- 🔍 **web_search** — Serper → DDG fallback  
- 🌤️ **get_weather** — OpenWeatherMap → estimated

*Agents invoke these tools at runtime via Gemini function calling.*
    """)
    st.markdown("---")
    st.markdown("""
    <div class="info-box">
    ⏱️ <b>Expected time:</b> 4–8 minutes<br>
    Agents actively search the web during execution.
    Each agent sees previous agents' outputs as context.
    </div>
    """, unsafe_allow_html=True)

# ── Input Form ────────────────────────────────────────────────────────────────
st.markdown("### 🗺️ Where are you going?")

col1, col2, col3, col4, col5 = st.columns([2.2, 2.2, 1.6, 1.6, 1.2])
with col1:
    source = st.text_input("📍 From", placeholder="e.g. Delhi, Kolkata, Mumbai")
with col2:
    destination = st.text_input("🏁 To", placeholder="e.g. Goa, Manali, Jaipur")
with col3:
    from_date = st.date_input("📅 Departure",
                               value=date.today() + timedelta(days=7),
                               min_value=date.today())
with col4:
    to_date = st.date_input("📅 Return",
                             value=date.today() + timedelta(days=12),
                             min_value=date.today() + timedelta(days=1))
with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    plan_btn = st.button("🚀 Plan Trip", type="primary", use_container_width=True)

# ── Execution ─────────────────────────────────────────────────────────────────
if plan_btn:
    errors = []
    if not source.strip():          errors.append("Please enter a departure city.")
    if not destination.strip():     errors.append("Please enter a destination city.")
    if source.strip().lower() == destination.strip().lower():
        errors.append("Source and destination must be different.")
    if to_date <= from_date:        errors.append("Return date must be after departure.")
    if not os.getenv("GEMINI_API_KEY"):
        errors.append("Gemini API key is required — enter it in the sidebar.")

    if errors:
        for e in errors: st.error(f"❌ {e}")
        st.stop()

    num_days = (to_date - from_date).days
    src    = source.strip().title()
    dest   = destination.strip().title()
    fd     = from_date.strftime("%Y-%m-%d")
    td     = to_date.strftime("%Y-%m-%d")
    fd_fmt = from_date.strftime("%d %b")
    td_fmt = to_date.strftime("%d %b %Y")

    st.markdown(f"""
    <div class="status-running">
        ⏳ Planning your <b>{num_days}-day trip</b>: <b>{src}</b> → <b>{dest}</b>
        &nbsp;({fd_fmt} – {td_fmt})<br>
        <small>Agents are actively searching the web using MCP tools. Takes 4–8 minutes.</small>
    </div>
    """, unsafe_allow_html=True)

    progress_bar       = st.progress(0)
    status_placeholder = st.empty()
    log_placeholder    = st.empty()

    result_box: dict = {}
    error_box:  dict = {}

    # Background thread — NO Streamlit calls
    def crew_worker():
        try:
            from crew import run_travel_crew
            result_box["data"] = run_travel_crew(
                source=src, destination=dest,
                from_date=fd, to_date=td,
            )
        except Exception as exc:
            import traceback
            error_box["msg"] = str(exc)
            error_box["tb"]  = traceback.format_exc()

    thread = threading.Thread(target=crew_worker, daemon=True)
    thread.start()

    # Main thread — all UI updates here
    steps = [
        ( 8, "🧠 Planner: checking today's date via MCP tool..."),
        (16, "🧠 Planner: searching route & transport options..."),
        (24, "🧠 Planner: finalizing execution strategy..."),
        (34, "✈️ Travel Agent: searching flights..."),
        (42, "✈️ Travel Agent: searching trains & buses..."),
        (52, "🏨 Hotel Agent: searching accommodation options..."),
        (62, "📍 Info Agent: fetching live weather data..."),
        (70, "📍 Info Agent: searching food & attractions..."),
        (80, "📅 Itinerary Agent: building day-by-day plan..."),
        (91, "📅 Itinerary Agent: calculating budget summary..."),
        (97, "✅ Finalizing your complete travel report..."),
    ]

    log_lines: list[str] = []
    idx = 0
    while thread.is_alive():
        if idx < len(steps):
            pct, msg = steps[idx]
            progress_bar.progress(pct)
            status_placeholder.markdown(f"**Status:** {msg}")
            log_lines.append(msg)
            log_placeholder.caption("  ·  ".join(log_lines[-3:]))
            idx += 1
        time.sleep(22)
    thread.join()

    if error_box:
        progress_bar.empty()
        status_placeholder.empty()
        log_placeholder.empty()
        st.markdown(f"""
        <div class="status-error">
            ❌ <b>Error:</b> {error_box['msg']}<br><br>
            <b>Common causes:</b><br>
            • Invalid Gemini key (must start with <code>AIza</code>)<br>
            • Gemini quota exceeded — wait 60s and retry<br>
            • Network issue
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🔍 Full traceback"):
            st.code(error_box.get("tb", ""))
        st.stop()

    progress_bar.progress(100)
    status_placeholder.empty()
    log_placeholder.empty()

    results = result_box.get("data", {})

    st.markdown(f"""
    <div class="status-done">
        ✅ <b>Your {num_days}-day trip to {dest} is ready!</b>
        Agents made live tool calls to search flights, hotels, weather, and attractions.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    tab_plan, tab_travel, tab_hotel, tab_info, tab_itin = st.tabs([
        "📋 Plan", "✈️ Transport", "🏨 Hotels", "📍 Destination", "📅 Itinerary"
    ])

    with tab_plan:
        st.markdown("### 🧠 Planner Agent — Execution Strategy")
        st.caption("Route analysis, transport recommendation, per-agent focus areas.")
        st.markdown(results.get("plan", "*No output.*"))

    with tab_travel:
        st.markdown(f"### ✈️ Transport: {src} → {dest}")
        st.caption("3 options per mode (cheapest · earliest · night). Return journey included.")
        st.markdown(results.get("travel", "*No output.*"))

    with tab_hotel:
        st.markdown(f"### 🏨 Hotels in {dest}")
        st.caption("3 hotels across 3 areas — transit hub · tourist centre · local neighbourhood.")
        st.markdown(results.get("hotels", "*No output.*"))

    with tab_info:
        st.markdown(f"### 📍 Destination Guide: {dest}")
        st.caption("Live weather · must-try food · top attractions · local tips.")
        st.markdown(results.get("information", "*No output.*"))

    with tab_itin:
        st.markdown(f"### 📅 Day-by-Day Itinerary ({num_days} days)")
        st.caption("Optimized by proximity. Morning → Afternoon → Evening per day.")
        st.markdown(results.get("itinerary", results.get("raw", "*No output.*")))

        full_report = "\n\n".join([
            f"SMART TRAVEL PLANNER — {src.upper()} TO {dest.upper()}",
            f"Dates: {fd_fmt} – {td_fmt}  ({num_days} days)",
            "=" * 60, "SECTION 1 — PLANNING ANALYSIS", "=" * 60,
            results.get("plan", ""),
            "=" * 60, "SECTION 2 — TRANSPORT OPTIONS", "=" * 60,
            results.get("travel", ""),
            "=" * 60, "SECTION 3 — HOTEL RECOMMENDATIONS", "=" * 60,
            results.get("hotels", ""),
            "=" * 60, "SECTION 4 — DESTINATION GUIDE", "=" * 60,
            results.get("information", ""),
            "=" * 60, "SECTION 5 — FULL ITINERARY", "=" * 60,
            results.get("itinerary", ""),
            "", "Generated by Smart Travel Planner (CrewAI + MCP + Gemini 2.5 Flash)",
        ])
        st.download_button(
            label="⬇️ Download Full Trip Report (.txt)",
            data=full_report,
            file_name=f"trip_{src}_{dest}_{fd}.txt".replace(" ", "_"),
            mime="text/plain",
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("🚀 Setup"):
    st.markdown("""
```bash
pip install -r requirements.txt
cp .env.example .env
# Set GEMINI_API_KEY=AIza... in .env
streamlit run app.py
```
| Key | Required | Free | Link |
|-----|----------|------|------|
| `GEMINI_API_KEY` | ✅ Yes | ✅ Yes | [aistudio.google.com](https://aistudio.google.com) |
| `SERPER_API_KEY` | Recommended | ✅ 2500/mo | [serper.dev](https://serper.dev) |
| `OPENWEATHER_API_KEY` | No | ✅ Yes | [openweathermap.org](https://openweathermap.org/api) |
    """)

with st.expander("🏗️ How MCP tools work here"):
    st.markdown("""
```
Agent runtime (Gemini function calling):

  Planner Agent
    │─── calls get_current_date() ──→ "Sunday, April 19, 2026" (real)
    │─── calls web_search("Delhi to Goa transport") ──→ live results
    └──→ produces execution plan

  Travel Agent  
    │─── calls web_search("flights Delhi Goa April 2026") ──→ live results
    │─── calls web_search("trains Delhi Goa") ──→ live results
    └──→ produces transport options

  Hotel Agent
    └─── calls web_search("hotels Goa near airport") ──→ live results

  Info Agent
    │─── calls get_weather("Goa", "2026-04-26") ──→ live weather
    │─── calls web_search("must try food Goa") ──→ live results
    └──→ produces destination guide

  Itinerary Agent
    └──→ synthesizes all above into day-by-day plan
```
Tool calls happen **inside** agent execution — Gemini decides when and what to search.
This is genuine MCP-style agentic tool use.
    """)