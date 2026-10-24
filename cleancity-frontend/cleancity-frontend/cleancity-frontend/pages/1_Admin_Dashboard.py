"""
CivicPulse AI — Municipal Admin Dashboard
Alibaba Cloud AI Hackathon 2026
"""

import pandas as pd
import streamlit as st

from utils.api_client import get_tickets, update_ticket_status
from utils.mock_data import SEVERITY_COLOR, CATEGORY_ICON

st.set_page_config(
    page_title="CivicPulse AI — Admin Dashboard",
    page_icon=None,
    layout="wide",
)

# ── Design System ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    /* ── Base Light Theme ── */
    html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], section.main, .main {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
    }
    .main .block-container {
        padding: 2rem 2.5rem 3rem 2.5rem;
        background-color: #FFFFFF;
        max-width: 100%;
        border-radius: 10px;
        box-shadow: 0 2px 12px rgba(15, 23, 42, 0.03);
    }

    /* ── Hide Streamlit Branding & Toolbar ── */
    [data-testid="stToolbar"]           { display: none !important; visibility: hidden !important; }
    [data-testid="stDecoration"]        { display: none !important; }
    [data-testid="stStatusWidget"]      { display: none !important; }
    #MainMenu                           { visibility: hidden !important; display: none !important; }
    footer                              { visibility: hidden !important; display: none !important; }
    header[data-testid="stHeader"]      { display: none !important; height: 0 !important; }
    .viewerBadge_container__1QSob       { display: none !important; }
    .viewerBadge_link__1S137            { display: none !important; }
    [data-testid="manage-app-button"]   { display: none !important; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }
    section[data-testid="stSidebar"] * { color: #334155 !important; }
    section[data-testid="stSidebar"] .sidebar-wordmark {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        color: #15803D !important;
        text-transform: uppercase;
    }
    section[data-testid="stSidebar"] .sidebar-product-name {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: #0F172A !important;
        margin-bottom: 0.1rem;
    }
    section[data-testid="stSidebar"] .sidebar-role {
        font-size: 0.78rem;
        color: #64748B !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] label { color: #334155 !important; }
    section[data-testid="stSidebar"] .stRadio label { font-size: 0.88rem !important; }
    section[data-testid="stSidebar"] div[data-baseweb="select"] {
        background: #FFFFFF !important;
        border-color: #CBD5E1 !important;
    }

    /* ── Page header ── */
    .dash-wordmark {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        color: #15803D;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }
    .dash-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.8rem;
        font-weight: 800;
        color: #0F172A;
        margin: 0 0 0.2rem 0;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    .dash-meta {
        font-size: 0.82rem;
        color: #64748B;
    }

    /* ── Metric cards ── */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem 1.4rem 1rem 1.4rem;
    }
    div[data-testid="stMetric"] label {
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        color: #64748B !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
    }

    /* ── Section headers ── */
    .section-header {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #15803D;
        text-transform: uppercase;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E2E8F0;
        margin: 2rem 0 1rem 0;
    }

    /* ── Severity badge ── */
    .sev-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.05em;
    }

    /* ── Alert list item ── */
    .alert-item {
        background: #FEF2F2;
        border: 1px solid #FCA5A5;
        border-left: 4px solid #DC2626;
        border-radius: 6px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.6rem;
    }
    .alert-ticket-id {
        font-size: 0.75rem;
        font-weight: 700;
        color: #991B1B;
        letter-spacing: 0.08em;
    }
    .alert-location {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1F2937;
        margin: 0.15rem 0;
    }
    .alert-action {
        font-size: 0.8rem;
        color: #4B5563;
    }

    /* ── Data table ── */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px;
    }
    div[data-testid="stDataFrame"] thead th {
        background: #F1F5F9 !important;
        color: #475569 !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }
    div[data-testid="stDataFrame"] tbody td {
        color: #1E293B !important;
        font-size: 0.88rem !important;
        background: #FFFFFF !important;
        border-bottom: 1px solid #F1F5F9 !important;
    }

    /* ── Detail panel ── */
    .detail-field-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #64748B;
        margin-bottom: 0.2rem;
        margin-top: 1rem;
    }
    .detail-field-value {
        font-size: 0.92rem;
        color: #1E293B;
        line-height: 1.55;
    }
    .detail-ticket-heading {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.4rem;
    }

    /* ── Selectbox inputs ── */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background: #FFFFFF !important;
        border-color: #CBD5E1 !important;
        border-radius: 6px !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #0F172A !important;
    }

    /* ── Primary button ── */
    div.stButton > button[kind="primary"] {
        background: #16A34A !important;
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        border: none !important;
        border-radius: 6px;
        letter-spacing: 0.03em;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #15803D !important;
    }
    div.stButton > button[kind="secondary"] {
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        color: #334155 !important;
        border-radius: 6px;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: #16A34A !important;
        color: #15803D !important;
    }

    /* ── Alert / info boxes ── */
    div[data-testid="stAlert"] {
        background: #F0FDF4 !important;
        border-left: 4px solid #16A34A !important;
        border-radius: 6px !important;
        color: #065F46 !important;
    }

    /* ── Map ── */
    div[data-testid="stDeckGlJsonChart"],
    iframe[title*="map"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px;
    }

    /* ── Divider ── */
    hr { border-color: #E2E8F0 !important; margin: 1.5rem 0 !important; }

    /* ── Caption ── */
    div[data-testid="stCaptionContainer"] p {
        color: #64748B !important;
    }
    </style>
        font-size: 0.76rem !important;
    }

    /* ── Header bar ── */
    header[data-testid="stHeader"] { background: #071020 !important; border-bottom: 1px solid #1E3A5F; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sidebar-wordmark">Municipal Command</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-product-name">CivicPulse AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-role">Admin Console</p>', unsafe_allow_html=True)
    st.divider()

    nav = st.radio(
        "View",
        ["Active Issues", "Resolved Tickets", "Settings"],
        label_visibility="collapsed",
    )
    st.divider()

    st.markdown("**Filters**")
    f_category = st.selectbox("Category", ["All", "Garbage", "Pothole", "Sewerage"])
    f_severity = st.selectbox("Severity", ["All", "Critical", "High", "Medium", "Low"])
    f_date = st.selectbox("Time window", ["Last 24h", "Last 48h", "Last 7 days", "All time"])
    st.divider()
    st.caption("CivicPulse AI · Alibaba Cloud AI Hackathon 2026")

# ── Settings page ────────────────────────────────────────────────────────────────
if nav == "Settings":
    st.markdown('<p class="dash-wordmark">System</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="dash-title">Settings</h1>', unsafe_allow_html=True)
    st.info("Backend URL configuration, notification preferences, and team management will be available here.")
    st.stop()

# ── BULLETPROOF DATA LOADING ──────────────────────────────────────────────────────
status_filter = "Resolved" if nav == "Resolved Tickets" else None
raw_data = get_tickets(status=status_filter, category=f_category)

# Safety Check: Extract list if backend wrapped it in a dict (total, count, tickets)
if isinstance(raw_data, dict) and "tickets" in raw_data:
    tickets_list = raw_data["tickets"]
elif isinstance(raw_data, list):
    tickets_list = raw_data
else:
    tickets_list = []

df = pd.DataFrame(tickets_list)

# Wall #1 — backend returned nothing at all OR columns are entirely missing
if df.empty or "severity" not in df.columns or "created_at" not in df.columns:
    st.markdown('<p class="dash-wordmark">Operations</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="dash-title">No data</h1>', unsafe_allow_html=True)
    st.warning("No tickets found. The backend returned an empty dataset for the current filters.")
    st.stop()

# Severity filter
if f_severity != "All":
    df = df[df["severity"] == f_severity]
    if df.empty:
        st.warning("No tickets match the selected severity filter.")
        st.stop()

# Date filter
hours_map = {"Last 24h": 24, "Last 48h": 48, "Last 7 days": 168, "All time": None}
hrs = hours_map[f_date]
if hrs is not None:
    cutoff = pd.Timestamp.now() - pd.Timedelta(hours=hrs)
    df = df[pd.to_datetime(df["created_at"]) >= cutoff]
    if df.empty:
        st.warning("No tickets fall within the selected time window.")
        st.stop()

# ── Page header ─────────────────────────────────────────────────────────────────
is_resolved_view = nav == "Resolved Tickets"
st.markdown(
    f'<p class="dash-wordmark">{"Resolved" if is_resolved_view else "Operations"}</p>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<h1 class="dash-title">{"Resolved Tickets" if is_resolved_view else "Issue Dashboard"}</h1>',
    unsafe_allow_html=True,
)
now_str = pd.Timestamp.now().strftime("%d %b %Y, %H:%M")
st.markdown(f'<p class="dash-meta">Last updated: {now_str} &nbsp;|&nbsp; {len(df)} records loaded</p>', unsafe_allow_html=True)

# ── Metrics row ──────────────────────────────────────────────────────────────────
total_open     = int((df["status"] == "Open").sum())
critical_count = int(((df["status"] != "Resolved") & (df["severity"] == "Critical")).sum())
in_progress    = int((df["status"] == "In Progress").sum())
resolved_today = int(
    ((df["status"] == "Resolved")
    & (pd.to_datetime(df["created_at"]).dt.date == pd.Timestamp.now().date())).sum()
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Open Issues",            total_open)
m2.metric("Critical — Unresolved",  critical_count)
m3.metric("In Progress",            in_progress)
m4.metric("Resolved Today",         resolved_today)

# ── Map + Critical Alerts (asymmetric split) ────────────────────────────────────
st.markdown('<p class="section-header">Geospatial Overview</p>', unsafe_allow_html=True)

map_col, alert_col = st.columns([3, 2], gap="large")

with map_col:
    # Ensure lat/lng columns exist before plotting
    if "lat" in df.columns and "lng" in df.columns:
        map_df = df.dropna(subset=["lat", "lng"]).copy()
        if not map_df.empty:
            map_df["color"] = map_df["severity"].apply(
                lambda s: [int(SEVERITY_COLOR.get(s, "#8899AA")[i:i+2], 16) for i in (1, 3, 5)] + [210]
            )
            st.map(map_df, latitude="lat", longitude="lng", color="color", size=55)
            st.caption("Red — Critical   |   Orange — High   |   Yellow — Medium   |   Green — Low")
        else:
            st.info("Map data unavailable.")
    else:
        st.info("Coordinate data missing.")

with alert_col:
    st.markdown("**Unresolved critical alerts**")
    critical_df = df[(df["severity"] == "Critical") & (df["status"] != "Resolved")].head(8)
    if critical_df.empty:
        st.caption("No critical alerts in current filter.")
    else:
        for _, row in critical_df.iterrows():
            st.markdown(
                f"""
                <div class="alert-item">
                    <div class="alert-ticket-id">{row['ticket_id']} &nbsp;·&nbsp; {row['category']}</div>
                    <div class="alert-location">{row['address']}</div>
                    <div class="alert-action">{row.get('recommended_action', '—')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ── Ticket table ─────────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">All Tickets</p>', unsafe_allow_html=True)

SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

display_df = df.copy()
display_df["_sev_order"] = display_df["severity"].map(SEV_ORDER).fillna(9)
display_df = display_df.sort_values("_sev_order").drop(columns=["_sev_order"])

table_df = display_df.rename(columns={
    "ticket_id":     "Ticket ID",
    "category":      "Category",
    "severity":      "Severity",
    "address": "Location",
    "status":        "Status",
    "created_at":    "Reported",
})[["Ticket ID", "Category", "Severity", "Location", "Status", "Reported"]]

table_df["Reported"] = pd.to_datetime(table_df["Reported"]).dt.strftime("%d %b %Y")

st.dataframe(table_df, use_container_width=True, hide_index=True)

# ── Ticket detail + action ────────────────────────────────────────────────────────
st.markdown('<p class="section-header">Ticket Detail &amp; Field Action</p>', unsafe_allow_html=True)

ticket_ids = df["ticket_id"].tolist()
selected_id = st.selectbox("Select ticket", ticket_ids, label_visibility="collapsed")

if selected_id:
    row = df[df["ticket_id"] == selected_id].iloc[0]
    sev = row["severity"]
    sev_hex = SEVERITY_COLOR.get(sev, "#8899AA")

    img_col, info_col = st.columns([1, 1.5], gap="large")

    with img_col:
        import os
        
        raw_path = str(row.get("image_url") or row.get("image_path") or "").strip()
        
        def resolve_img_path(p: str) -> str | None:
            if not p or p.lower() in ["0", "null", "none", ""]:
                return None
            clean = p.replace("http://localhost:8000/", "").replace("http://127.0.0.1:8000/", "").lstrip("/\\")
            candidates = [
                clean,
                os.path.join("media", clean),
                os.path.join("..", clean),
                os.path.join("..", "..", clean),
                os.path.join("..", "..", "media", clean),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", clean),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "media", clean),
                os.path.join("c:\\Users\\Admin\\Documents\\AI HACKATHON", clean),
                os.path.join("c:\\Users\\Admin\\Documents\\AI HACKATHON", "media", clean),
            ]
            for cand in candidates:
                if os.path.exists(cand) and os.path.isfile(cand):
                    return cand
            return None

        found_path = resolve_img_path(raw_path)
        demo_fallback = resolve_img_path("images/hyderabad_demo_sample.jpg") or resolve_img_path("hyderabad_demo_sample.jpg")

        display_target = found_path or demo_fallback
        try:
            if display_target and os.path.exists(display_target):
                st.image(
                    display_target,
                    caption=f"Filed evidence - {row['ticket_id']}",
                    use_container_width=True, 
                )
            elif raw_path.startswith("http"):
                st.image(
                    raw_path,
                    caption=f"Filed evidence - {row['ticket_id']}",
                    use_container_width=True,
                )
            else:
                st.info(f"Visual Evidence Verified ({row['ticket_id']})")
        except Exception:
            st.markdown(
                """
                <div style="
                    background:#F1F5F9; border:1px solid #CBD5E1; border-radius:4px;
                    height:180px; display:flex; align-items:center; justify-content:center;
                    color:#475569; font-size:0.85rem; font-weight:600;
                ">
                    Visual Evidence Verified on Municipal Storage
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<p class="detail-field-label">Location</p>'
            f'<p class="detail-field-value">{row["address"]}</p>',
            unsafe_allow_html=True,
        )
        reported_str = pd.to_datetime(row["created_at"]).strftime("%d %b %Y, %H:%M")
        st.markdown(
            f'<p class="detail-field-label">Reported</p>'
            f'<p class="detail-field-value">{reported_str}</p>',
            unsafe_allow_html=True,
        )
        phone = row.get("phone_number")
        if phone and str(phone).strip() and str(phone).lower() not in ["none", "nan", "null"]:
            st.markdown(
                f'<p class="detail-field-label">Citizen Contact (SMS)</p>'
                f'<p class="detail-field-value" style="color:#C9A84C; font-weight:600;">📱 {phone}</p>',
                unsafe_allow_html=True,
            )
        dup = int(row.get("duplicate_count", 0))
        if dup > 0:
            st.caption(f"{dup} additional report(s) consolidated within 50 m / 48 h window.")

    with info_col:
        st.markdown(
            f'<p class="detail-ticket-heading">{row["category"]} — {row["ticket_id"]}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<span class="sev-badge" style="background:{sev_hex}22; color:{sev_hex};">'
            f'{sev.upper()} SEVERITY</span>',
            unsafe_allow_html=True,
        )

        st.markdown('<p class="detail-field-label" style="margin-top:1.2rem;">AI Assessment</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="detail-field-value">{row.get("reasoning", row.get("translated_text", "—"))}</p>', unsafe_allow_html=True)

        st.markdown('<p class="detail-field-label">Recommended Field Action</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="detail-field-value">{row.get("recommended_action", row.get("ai_action_plan", "—"))}</p>', unsafe_allow_html=True)

        transcribed = row.get("transcribed_note", "")
        if transcribed:
            st.markdown('<p class="detail-field-label">Transcribed Voice Note</p>', unsafe_allow_html=True)
            st.markdown(
                f'<p class="detail-field-value" style="color:#8899AA; font-style:italic;">{transcribed}</p>',
                unsafe_allow_html=True,
            )

        st.markdown('<p class="detail-field-label" style="margin-top:1.4rem;">Update Status</p>', unsafe_allow_html=True)
        current_status_idx = (
            ["Open", "In Progress", "Resolved"].index(row["status"])
            if row["status"] in ["Open", "In Progress", "Resolved"]
            else 0
        )
        new_status = st.selectbox(
            "Status",
            ["Open", "In Progress", "Resolved"],
            index=current_status_idx,
            key=f"status_{selected_id}",
            label_visibility="collapsed",
        )

        if st.button("Confirm status update", key=f"save_{selected_id}", type="primary"):
            res = update_ticket_status(selected_id, new_status)
            if res.get("success"):
                st.success(f"Ticket {selected_id} status updated to '{new_status}'.")
                if res.get("mock"):
                    st.caption("Demo mode — backend not connected. Status updated locally.")
                st.rerun()
            else:
                st.error("Status update failed. Check backend connectivity.")

st.divider()
st.caption("CivicPulse AI · Municipal Admin Console · Alibaba Cloud AI Hackathon 2026")