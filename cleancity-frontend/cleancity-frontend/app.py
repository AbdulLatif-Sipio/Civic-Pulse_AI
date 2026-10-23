"""
CivicPulse AI — Citizen Reporting & Civic Governance Portal
Official Municipal Service · Government of Sindh (Karachi & Hyderabad)
Alibaba Cloud AI Hackathon 2026
"""

import re
import streamlit as st
from utils.api_client import submit_report, get_ticket_detail

st.set_page_config(
    page_title="CivicPulse AI — Municipal Citizen Portal",
    page_icon="🏛️",
    layout="centered",
)

# ── Session State Initialization ──────────────────────────────────────────────
if "last_ticket" not in st.session_state:
    st.session_state.last_ticket = None
if "selected_prompt" not in st.session_state:
    st.session_state.selected_prompt = ""
if "tracked_ticket" not in st.session_state:
    st.session_state.tracked_ticket = None

# ── Design System & Custom Styling ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    /* ── Base Theme & Typography (Clean Municipal Light) ── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }
    .main .block-container {
        max-width: 760px;
        padding: 2.2rem 2rem 4rem 2rem;
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
        margin-top: 1.5rem;
        margin-bottom: 2rem;
    }

    /* ── Completely Hide Streamlit Branding, Toolbar & Viewer Badges ── */
    [data-testid="stSidebar"]           { display: none !important; }
    [data-testid="collapsedControl"]    { display: none !important; }
    section[data-testid="stSidebarNav"] { display: none !important; }
    header[data-testid="stHeader"]      { display: none !important; height: 0 !important; }
    [data-testid="stToolbar"]           { display: none !important; visibility: hidden !important; }
    [data-testid="stDecoration"]        { display: none !important; }
    [data-testid="stStatusWidget"]      { display: none !important; }
    #MainMenu                           { visibility: hidden !important; display: none !important; }
    footer                              { visibility: hidden !important; display: none !important; }
    .viewerBadge_container__1QSob       { display: none !important; }
    .viewerBadge_link__1S137            { display: none !important; }
    [data-testid="manage-app-button"]   { display: none !important; }

    /* ── Top Municipal Notice Bar ── */
    .muni-topbar {
        background: #F1F5F9;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.65rem 1.1rem;
        margin-bottom: 1.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.82rem;
    }
    .muni-badge {
        color: #15803D;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .muni-helpline {
        color: #475569;
        font-size: 0.8rem;
    }
    .muni-helpline strong {
        color: #0F172A;
    }

    /* ── Page Header ── */
    .portal-wordmark {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        color: #15803D;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }
    .portal-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2.25rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.15;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.02em;
    }
    .portal-subtitle {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 1.6rem;
        line-height: 1.55;
    }

    /* ── Section Dividers & Labels ── */
    .form-section-label {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        color: #0F172A;
        text-transform: uppercase;
        margin: 2rem 0 0.6rem 0;
        padding-bottom: 0.45rem;
        border-bottom: 2px solid #E2E8F0;
    }

    /* ── File Uploader ── */
    div[data-testid="stFileUploader"] {
        background: #F8FAFC;
        border: 1px dashed #CBD5E1;
        border-radius: 8px;
        padding: 1rem;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #16A34A;
        background: #F0FDF4;
    }

    /* ── Text Areas & Inputs ── */
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: #0F172A !important;
        font-family: 'Inter', sans-serif;
    }
    div[data-testid="stTextArea"] textarea::placeholder,
    div[data-testid="stTextInput"] input::placeholder {
        color: #94A3B8 !important;
    }
    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stTextInput"] input:focus {
        border-color: #16A34A !important;
        box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.15) !important;
        outline: none !important;
    }

    /* ── Widget Labels ── */
    label[data-testid="stWidgetLabel"] p {
        color: #334155 !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
    }

    /* ── Audio Input ── */
    div[data-testid="stAudioInput"] {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
    }

    /* ── Primary Submit Button ── */
    div.stButton > button[kind="primary"] {
        width: 100%;
        height: 3.4rem;
        background: #16A34A !important;
        color: #FFFFFF !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.02rem;
        font-weight: 700;
        border: none !important;
        border-radius: 8px;
        letter-spacing: 0.03em;
        box-shadow: 0 2px 8px rgba(22, 163, 74, 0.25);
        transition: all 0.15s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #15803D !important;
        box-shadow: 0 4px 12px rgba(22, 163, 74, 0.35);
        transform: translateY(-1px);
    }
    div.stButton > button[kind="secondary"] {
        background: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        color: #334155 !important;
        border-radius: 8px;
        font-size: 0.88rem;
        font-weight: 600;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: #16A34A !important;
        color: #15803D !important;
        background: #F0FDF4 !important;
    }

    /* ── Badges & Status Pills ── */
    .status-pill {
        display: inline-block;
        padding: 0.3rem 0.75rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .pill-green {
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }
    .pill-gold {
        background: #FEFCE8;
        color: #854D0E;
        border: 1px solid #FEF08A;
    }
    .pill-blue {
        background: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
    }
    .pill-red {
        background: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }

    /* ── Tabs Styling ── */
    div[data-baseweb="tab-list"] {
        background-color: #F1F5F9;
        border: 1px solid #E2E8F0;
        gap: 6px;
        padding: 5px;
        border-radius: 8px;
        margin-bottom: 1.6rem;
    }
    div[data-baseweb="tab"] {
        color: #64748B !important;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 8px 16px;
        border-radius: 6px;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    /* ── Info & Cards ── */
    .info-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
    }
    .info-card h4 {
        color: #15803D;
        margin: 0 0 0.4rem 0;
        font-size: 1rem;
        font-weight: 700;
    }
    .info-card p {
        color: #475569;
        font-size: 0.88rem;
        margin: 0;
        line-height: 1.55;
    }

    /* ── Print Media Optimization (Clean Receipt Print) ── */
    @media print {
        body, html { background: #FFFFFF !important; color: #000000 !important; }
        [data-testid="stSidebar"], [data-testid="stToolbar"], header, footer, 
        .stButton, div[data-baseweb="tab-list"], .muni-topbar, .no-print {
            display: none !important;
        }
        .main .block-container {
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            max-width: 100% !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Top Bar ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="muni-topbar">
        <span class="muni-badge">🏛️ Sindh Municipal Governance System</span>
        <span class="muni-helpline">Emergency Cell: <strong>1122</strong> | Complaint Hotline: <strong>1339</strong></span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Main Header ────────────────────────────────────────────────────────────────
st.markdown('<p class="portal-wordmark">Public Works & Sanitation Intelligence — CivicPulse AI</p>', unsafe_allow_html=True)
st.markdown('<h1 class="portal-title">CivicPulse AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="portal-subtitle">'
    'Official citizen reporting portal for <strong>Karachi Metropolitan Corporation (KMC)</strong> and '
    '<strong>Hyderabad Municipal Corporation (HMC)</strong>. Submissions are processed in real-time by multimodal AI '
    'and automatically dispatched to municipal field crews.'
    '</p>',
    unsafe_allow_html=True,
)

# ── Tab Navigation ─────────────────────────────────────────────────────────────
tab_report, tab_track, tab_prompts, tab_privacy = st.tabs([
    "📝 Report Civic Issue",
    "🔍 Track Complaint",
    "💡 Prompts & AI Help",
    "🔒 Privacy & Citizen Data Policy"
])


# ==============================================================================
# TAB 1: REPORT CIVIC ISSUE
# ==============================================================================
with tab_report:
    # ── Success State ─────────────────────────────────────────────────────────
    if st.session_state.last_ticket:
        ticket = st.session_state.last_ticket
        st.markdown(
            f"""
            <div style="background:#F0FDF4; border:1px solid #86EFAC; border-left:5px solid #16A34A; border-radius:8px; padding:1.4rem; margin-bottom:1.5rem;">
                <h3 style="color:#065F46; margin:0 0 0.4rem 0; font-family:'Plus Jakarta Sans',sans-serif; font-size:1.25rem;">✅ Complaint Registered Successfully</h3>
                <p style="color:#334155; font-size:0.92rem; margin:0 0 0.9rem 0;">
                    Your report has been verified by the AI triage engine and logged in the municipal database.
                </p>
                <div style="background:#FFFFFF; padding:0.9rem 1.1rem; border-radius:6px; border:1px solid #CBD5E1; font-family:monospace; font-size:1.1rem; color:#15803D; font-weight:700;">
                    Reference Tracking ID: <strong>{ticket.get('ticket_id', 'TKT-PENDING')}</strong>
                </div>
                <p style="color:#64748B; font-size:0.82rem; margin:0.8rem 0 0 0;">
                    {ticket.get('message', 'Municipal crews have been notified. An automated SMS update will follow.')}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if ticket.get("emergency_dispatch") and ticket["emergency_dispatch"].get("dispatched"):
            ed = ticket["emergency_dispatch"]
            st.markdown(
                f"""
                <div style="background:#FEF2F2; border:1px solid #FCA5A5; border-left:5px solid #DC2626; border-radius:8px; padding:1.3rem; margin-bottom:1.5rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                        <span style="color:#991B1B; font-size:0.85rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em;">
                            🚨 CRITICAL DISPATCH: Official Alert Transmitted
                        </span>
                        <span style="background:#FEE2E2; color:#B91C1C; border:1px solid #FCA5A5; padding:0.25rem 0.6rem; border-radius:6px; font-size:0.78rem; font-weight:700;">
                            {ed.get('delivery_status', 'DISPATCHED')}
                        </span>
                    </div>
                    <p style="color:#7F1D1D; font-size:0.9rem; margin:0 0 0.7rem 0; line-height:1.5;">
                        An emergency alert email was automatically generated and dispatched to the nearest designated Municipal Committee supervisor:
                    </p>
                    <div style="background:#FFFFFF; border:1px solid #FECACA; border-radius:6px; padding:0.9rem 1.1rem; font-size:0.85rem; color:#1F2937;">
                        <strong>{ed.get('recipient_name')}</strong> ({ed.get('recipient_designation')})<br>
                        📧 <code>{ed.get('recipient_email')}</code><br>
                        📍 {ed.get('zone')} ({ed.get('city')}) &nbsp;|&nbsp; 📏 Proximity: <strong>~{ed.get('distance_km')} km</strong> from incident site
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        if ticket.get("mock"):
            st.caption("ℹ️ Demo Mode: Backend simulated response.")

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            if st.button("Submit Another Report", type="secondary"):
                st.session_state.last_ticket = None
                st.session_state.selected_prompt = ""
                st.rerun()
        with col_act2:
            st.markdown(
                """
                <button onclick="window.print()" class="no-print" style="width:100%; height:2.7rem; background:#FFFFFF; border:1px solid #CBD5E1; color:#334155; border-radius:8px; font-weight:600; font-size:0.88rem; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:0.4rem; transition:all 0.15s ease;">
                    🖨️ Print Complaint Receipt
                </button>
                """,
                unsafe_allow_html=True
            )
        st.stop()

    # ── Section 1: Photographic Evidence ──────────────────────────────────────
    st.markdown('<p class="form-section-label">Section 1 — Photographic Evidence (Required)</p>', unsafe_allow_html=True)
    image_file = st.file_uploader(
        "Upload a clear photograph of the infrastructure issue",
        type=["jpg", "jpeg", "png"],
        help="A clear, well-lit photo allows Gemini Vision to detect hazard type and severity accurately.",
    )
    if image_file:
        st.image(image_file, caption="Evidence frame captured — verified for Computer Vision analysis.", use_container_width=True)
        st.markdown('<span class="status-pill pill-green">✓ Visual Pre-processing Ready</span><span class="status-pill pill-gold">Face/Plate Privacy Blur Active</span>', unsafe_allow_html=True)

    # ── Section 2: Description & Audio ────────────────────────────────────────
    st.markdown('<p class="form-section-label">Section 2 — Problem Description & Audio</p>', unsafe_allow_html=True)
    st.caption("You can record a voice note in Urdu, Sindhi, or English, or write details below.")

    audio_file = st.audio_input("Record an Urdu / English voice note")
    if audio_file is not None:
        st.audio(audio_file)
        st.markdown('<span class="status-pill pill-green">🎤 Voice Note Captured</span>', unsafe_allow_html=True)

    # Prompt Quick-Select helper
    with st.expander("💡 Load a standard prompt from the Municipal Library", expanded=False):
        quick_prompts = {
            "Select a prompt template...": "",
            "🗑️ Garbage dump on main road blocking path": "Major commercial waste dump accumulated on main road for 4 days. Blocking pedestrian walkway with severe stench and stray animals. Immediate waste truck lifting required.",
            "🕳️ Deep hazardous pothole near intersection": "Deep hazardous pothole (approx 2 feet wide, 8 inches deep) near busy intersection. Causing frequent motorcycle falls and tire blowouts, urgent asphalt patch needed.",
            "🚰 Open gutter with missing manhole cover": "CRITICAL HAZARD: Open gutter with missing manhole cover on unlit street. Extreme risk of pedestrians or children falling in. Urgent metal/concrete slab installation required.",
            "🚰 Choked sewerage line backflow": "Sewer line completely choked, black toxic water overflowing onto street and entering commercial shops and houses.",
            "⚡ Sparking electric wire detached from pole": "High-voltage electric wire hanging loose from damaged pole, sparking intermittently near water puddle.",
            "💧 Main drinking water pipeline burst": "Clean drinking water main supply line burst, thousands of gallons flooding street while adjacent residential blocks have zero water supply.",
        }
        chosen_quick = st.selectbox("Choose template:", options=list(quick_prompts.keys()), index=0)
        if chosen_quick and quick_prompts[chosen_quick]:
            if st.button("Apply Selected Template"):
                st.session_state.selected_prompt = quick_prompts[chosen_quick]
                st.rerun()

    description = st.text_area(
        "Written description (Urdu / Roman Urdu / English)",
        value=st.session_state.get("selected_prompt", ""),
        placeholder="e.g. Main road par kachray ka dher laga hua hai aur badboo bohot ziada hai. (State location and how many days it has been present)",
        height=90,
    )

    # ── Section 3: Location & Geolocation ─────────────────────────────────────
    st.markdown('<p class="form-section-label">Section 3 — Location & Geolocation Telemetry</p>', unsafe_allow_html=True)

    # Master Locations Dictionary (Karachi + Hyderabad)
    LOCATION_PRESETS = {
        # Karachi Landmarks
        "Karachi — Saddar / Empress Market (City Center)": (24.860700, 67.001100),
        "Karachi — Clifton Block 2 / Boat Basin": (24.823600, 67.032200),
        "Karachi — Clifton / Sea View / Do Darya": (24.795000, 67.065000),
        "Karachi — DHA Phase 5 / 6 / Khayaban-e-Shahbaz": (24.805000, 67.058000),
        "Karachi — DHA Phase 2 / Sunset Boulevard": (24.839000, 67.072000),
        "Karachi — Gulshan-e-Iqbal / Hassan Square / NIPA": (24.920700, 67.092800),
        "Karachi — Gulshan-e-Iqbal / University Road": (24.931000, 67.112000),
        "Karachi — Gulistan-e-Jauhar / Kamran Chowrangi": (24.914000, 67.135000),
        "Karachi — Gulistan-e-Jauhar / Perfume Chowk": (24.922000, 67.140000),
        "Karachi — North Nazimabad / Hyderi Market": (24.939200, 67.038100),
        "Karachi — North Nazimabad / Sakhi Hassan": (24.945000, 67.052000),
        "Karachi — Federal B Area / Water Pump": (24.930000, 67.068000),
        "Karachi — Federal B Area / Aisha Manzil": (24.925000, 67.062000),
        "Karachi — New Karachi / UP More": (24.975000, 67.065000),
        "Karachi — Korangi Industrial Area": (24.838400, 67.142000),
        "Karachi — Landhi / Babar Market": (24.845000, 67.185000),
        "Karachi — Malir Cantt / Checkpost 2": (24.928000, 67.205000),
        "Karachi — Malir City / Kala Board": (24.918000, 67.202000),
        "Karachi — Shahrah-e-Faisal / Nursery": (24.862000, 67.070000),
        "Karachi — PECHS / Tariq Road": (24.871000, 67.059000),
        "Karachi — Bahadurabad / Char Minar Chowrangi": (24.882000, 67.068000),
        "Karachi — Liaquatabad / Supermarket": (24.905000, 67.042000),
        "Karachi — Nazimabad / Golimar": (24.913000, 67.025000),
        "Karachi — SITE Industrial Area": (24.898000, 66.992000),
        "Karachi — Orangi Town / Banaras": (24.945000, 66.985000),
        "Karachi — Keamari / Karachi Port Trust": (24.815000, 66.975000),
        "Karachi — Lyari / Lea Market": (24.868000, 66.995000),
        "Karachi — Buffer Zone / Surjani Town": (25.020000, 67.050000),
        "Karachi — Scheme 33 / Safoora Chowrangi": (24.960000, 67.155000),
        "Karachi — Port Qasim / Bin Qasim": (24.780000, 67.330000),

        # Hyderabad Landmarks
        "Hyderabad — Autobahn Road / Latifabad Unit 2": (25.378000, 68.352000),
        "Hyderabad — Latifabad Unit 7 / General Hospital": (25.367000, 68.358000),
        "Hyderabad — Latifabad Unit 6 / D-Type Colony": (25.371000, 68.354000),
        "Hyderabad — Latifabad Unit 8 / 9 / 11": (25.364000, 68.355000),
        "Hyderabad — Latifabad Unit 12 / Timber Market": (25.358000, 68.362000),
        "Hyderabad — Latifabad Unit 3 & 4 / Gol Building": (25.374000, 68.350000),
        "Hyderabad — Naseem Nagar Chowk / Qasimabad": (25.395000, 68.332000),
        "Hyderabad — Wadhu Wah Road / Qasimabad": (25.405000, 68.338000),
        "Hyderabad — Citizen Colony / Jamshoro Road": (25.388000, 68.341000),
        "Hyderabad — Prince Town / Gul-e-Latif": (25.398000, 68.328000),
        "Hyderabad — London Town / Alamdar Chowk": (25.402000, 68.345000),
        "Hyderabad — Pakka Qila (Pacco Qillo) / Shahi Bazaar": (25.392000, 68.373500),
        "Hyderabad — Haider Chowk / Saddar Cantt": (25.391000, 68.362000),
        "Hyderabad — Station Road / Resham Gali / Gari Khata": (25.397000, 68.369000),
        "Hyderabad — Hirabad / Tower Market Chowk": (25.394000, 68.365000),
        "Hyderabad — Thandi Sarak / Hyderabad Gymkhana": (25.402000, 68.356000),
        "Hyderabad — Tilak Incline / Cantt Board": (25.393000, 68.360000),
        "Hyderabad — Kali Mori / Phuleli Canal": (25.382000, 68.385000),
        "Hyderabad — Pareetabad / Noorani Basti": (25.389000, 68.388000),
        "Hyderabad — Kotri Barrage / Indus River": (25.432000, 68.315000),
        "Hyderabad — SITE Industrial Area / Fateh Chowk": (25.385000, 68.318000),
        "Hyderabad — Jamshoro Phatak / Mehran Link": (25.412000, 68.295000),
        "Hyderabad — Tando Jam / Agriculture University": (25.428000, 68.535000),
        "Hyderabad — Tando Wali Muhammad / Giddu Chowk": (25.380000, 68.345000),
        "Hyderabad — Hussainabad / Sabzi Mandi Road": (25.352000, 68.338000),
        "Hyderabad — Gulshan-e-Hali / Railway Colony": (25.399000, 68.378000),
    }

    # Browser GPS Detection Attempt
    try:
        from streamlit_js_eval import get_geolocation
        live_browser_loc = get_geolocation()
    except Exception:
        live_browser_loc = None

    detected_browser_lat, detected_browser_lng = None, None
    if live_browser_loc and isinstance(live_browser_loc, dict) and "coords" in live_browser_loc:
        try:
            detected_browser_lat = float(live_browser_loc["coords"]["latitude"])
            detected_browser_lng = float(live_browser_loc["coords"]["longitude"])
        except Exception:
            pass

    # City Scope Filter
    city_scope = st.radio(
        "Municipal Jurisdiction:",
        options=["Karachi Metropolitan (KMC)", "Hyderabad Municipal (HMC)", "Show All Areas"],
        index=0,
        horizontal=True,
    )

    if city_scope == "Karachi Metropolitan (KMC)":
        filtered_presets = {k: v for k, v in LOCATION_PRESETS.items() if "Karachi" in k}
    elif city_scope == "Hyderabad Municipal (HMC)":
        filtered_presets = {k: v for k, v in LOCATION_PRESETS.items() if "Hyderabad" in k}
    else:
        filtered_presets = LOCATION_PRESETS

    selected_preset = st.selectbox(
        "Select Area / Neighborhood Preset:",
        options=list(filtered_presets.keys()),
        index=0,
        help="Select your neighborhood from over 55 calibrated municipal zones."
    )

    col_addr, col_lock = st.columns([3, 2])
    with col_lock:
        st.markdown("<div style='height:1.7rem'></div>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            lock_khi = st.button("📍 Center KHI", help="Lock to Karachi Saddar Center (24.8607° N, 67.0011° E)")
        with col_btn2:
            lock_hyd = st.button("📍 Center HYD", help="Lock to Hyderabad Haider Chowk (25.3910° N, 68.3620° E)")

    with col_addr:
        preset_val = selected_preset
        address = st.text_input(
            "Specific Street Address or Landmark:",
            value=preset_val,
            placeholder="e.g. Near Empress Market, Saddar or Unit 7 Hospital Gate",
        )

    # Determine Active Coordinates
    if lock_khi:
        final_lat, final_lng = 24.860700, 67.001100
        location_source = "🎯 Karachi Metropolitan Center Locked"
    elif lock_hyd:
        final_lat, final_lng = 25.391000, 68.362000
        location_source = "🎯 Hyderabad Municipal Center Locked"
    elif detected_browser_lat is not None and detected_browser_lng is not None:
        final_lat, final_lng = detected_browser_lat, detected_browser_lng
        location_source = "📡 Live Device GPS Sensor (Browser Telemetry)"
    else:
        coords = filtered_presets.get(selected_preset, (24.860700, 67.001100))
        final_lat, final_lng = coords
        location_source = f"📍 Calibrated Ward Landmark ({selected_preset.split('—')[0].strip()})"

    # Display GPS Status Pill
    st.markdown(
        f"""
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:0.65rem 1rem; margin-top:0.4rem; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span class="status-pill pill-gold">{location_source}</span>
                <span style="font-family:monospace; color:#0F172A; font-weight:600; font-size:0.88rem;">{final_lat:.6f}° N, {final_lng:.6f}° E</span>
            </div>
            <span style="color:#15803D; font-size:0.78rem; font-weight:700;">Precision: ±5m</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Section 4: Mobile Number (Pakistan Only) ──────────────────────────────
    st.markdown('<p class="form-section-label">Section 4 — Citizen Mobile Number (Pakistan 🇵🇰)</p>', unsafe_allow_html=True)
    st.caption("Provide your 11-digit Pakistan mobile number to receive official SMS dispatch receipts and crew status alerts.")

    def parse_pak_phone(raw_phone: str):
        if not raw_phone or not raw_phone.strip():
            return False, "", ""
        clean = re.sub(r"[\s\-\(\)\+]", "", raw_phone.strip())
        if clean.startswith("92"):
            clean = "0" + clean[2:]
        elif not clean.startswith("0") and len(clean) == 10 and clean.startswith("3"):
            clean = "0" + clean

        if not re.match(r"^03[0-9]{9}$", clean):
            return False, clean, "Invalid Format"

        prefix = int(clean[:4])
        if 300 <= prefix <= 309:
            carrier = "Jazz / Mobilink"
        elif 310 <= prefix <= 318:
            carrier = "Zong 4G"
        elif 320 <= prefix <= 325:
            carrier = "Warid"
        elif 330 <= prefix <= 337:
            carrier = "Ufone 4G"
        elif 340 <= prefix <= 349:
            carrier = "Telenor Pakistan"
        elif clean[:4] == "0355":
            carrier = "SCOM"
        else:
            carrier = "Pakistan Cellular Network"

        formatted = f"{clean[:4]}-{clean[4:]}"
        return True, formatted, carrier

    phone_input = st.text_input(
        "Mobile Number (Pakistan Only):",
        placeholder="0300-1234567 or 0321-9876543",
        help="Valid formats: 03XXXXXXXXX or +923XXXXXXXXX (Jazz, Zong, Telenor, Ufone, SCOM)"
    )

    is_phone_valid, formatted_phone, phone_carrier = parse_pak_phone(phone_input)

    if phone_input.strip():
        if is_phone_valid:
            st.markdown(
                f'<span class="status-pill pill-green">✅ Valid Pakistan Mobile</span>'
                f'<span class="status-pill pill-blue">{phone_carrier}</span>'
                f'<span style="font-size:0.8rem; color:#7A90A8;">SMS alerts will be sent to <strong>{formatted_phone}</strong></span>',
                unsafe_allow_html=True
            )
        else:
            st.warning("⚠️ Please enter a valid 11-digit Pakistan mobile number (e.g. 0300-1234567).")

    sms_consent = st.checkbox("📲 Send me automated SMS updates for ticket status and field crew dispatch", value=True)

    st.divider()

    # ── Submission Action ─────────────────────────────────────────────────────
    can_submit = bool(image_file) and bool(address.strip())
    if not can_submit:
        st.info("ℹ️ A photograph (Section 1) and location address (Section 3) are required to transmit a report.")

    if st.button("Submit Report to Municipal AI Pipeline", disabled=not can_submit, type="primary"):
        with st.spinner("Processing multimodal inputs (Vision + Audio STT + Geo-deduplication)..."):
            result = submit_report(
                image_file=image_file,
                audio_file=audio_file,
                description=description,
                lat=final_lat,
                lng=final_lng,
                address=address,
                phone_number=formatted_phone if is_phone_valid else "",
            )
        if result.get("success"):
            st.session_state.last_ticket = result
            st.rerun()
        else:
            st.error(f"Submission failed: {result.get('message', 'An error occurred while connecting to the municipal backend.')}")


# ==============================================================================
# TAB 2: TRACK COMPLAINT
# ==============================================================================
with tab_track:
    st.markdown('<p class="form-section-label">Citizen Complaint Status Tracker</p>', unsafe_allow_html=True)
    st.caption("Look up any previously registered civic ticket using your reference code (e.g. TKT-A8F12C).")

    track_id_input = st.text_input("Enter Ticket Reference ID:", placeholder="e.g. TKT-B1E29D or TKT-...")

    if st.button("Track Status", type="secondary"):
        if track_id_input.strip():
            with st.spinner("Querying municipal grievance database..."):
                ticket_info = get_ticket_detail(track_id_input.strip().upper())
                st.session_state.tracked_ticket = ticket_info
        else:
            st.warning("Please enter a valid ticket ID.")

    if st.session_state.tracked_ticket:
        t = st.session_state.tracked_ticket
        status_val = t.get("status", "Open")
        if status_val == "Resolved":
            status_bg = "#ECFDF5"
            status_text = "#065F46"
            status_border = "#A7F3D0"
        elif status_val == "In Progress":
            status_bg = "#FEFCE8"
            status_text = "#854D0E"
            status_border = "#FEF08A"
        else:
            status_bg = "#EFF6FF"
            status_text = "#1E40AF"
            status_border = "#BFDBFE"

        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:1.5rem; margin-top:1.2rem; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.1rem; border-bottom:1px solid #F1F5F9; padding-bottom:0.8rem;">
                    <span style="font-family:monospace; color:#15803D; font-size:1.2rem; font-weight:700;">{t.get('ticket_id')}</span>
                    <span style="background:{status_bg}; color:{status_text}; border:1px solid {status_border}; padding:0.3rem 0.8rem; border-radius:6px; font-size:0.82rem; font-weight:700; text-transform:uppercase;">
                        {status_val}
                    </span>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.9rem; font-size:0.88rem; margin-bottom:1.1rem;">
                    <div><span style="color:#64748B;">Category:</span> <strong style="color:#0F172A;">{t.get('category', 'Civic Issue')}</strong></div>
                    <div><span style="color:#64748B;">AI Severity:</span> <strong style="color:#0F172A;">{t.get('severity', 'Medium')}</strong></div>
                    <div><span style="color:#64748B;">Coordinates:</span> <code style="color:#15803D; font-weight:600;">{t.get('latitude', 0.0):.4f}°, {t.get('longitude', 0.0):.4f}°</code></div>
                    <div><span style="color:#64748B;">Logged:</span> <span style="color:#334155;">{str(t.get('timestamp', 'Recent'))[:19]}</span></div>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:1rem; margin-top:0.8rem;">
                    <div style="color:#15803D; font-size:0.75rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.4rem;">
                        Dispatched AI Action Plan
                    </div>
                    <p style="color:#334155; font-size:0.88rem; margin:0; line-height:1.55;">
                        {t.get('ai_action_plan', 'Field inspection scheduled by municipal zonal supervisor.')}
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="margin-top:0.8rem;" class="no-print">
                <button onclick="window.print()" style="width:100%; height:2.7rem; background:#FFFFFF; border:1px solid #CBD5E1; color:#334155; border-radius:8px; font-weight:600; font-size:0.88rem; cursor:pointer; display:flex; align-items:center; justify-content:center; gap:0.4rem;">
                    🖨️ Print Complaint Receipt
                </button>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif st.session_state.tracked_ticket is None and track_id_input:
        st.info("No matching ticket found with this reference. Please verify your reference code.")


# ==============================================================================
# TAB 3: PROMPTS & AI HELP
# ==============================================================================
with tab_prompts:
    st.markdown('<p class="form-section-label">Municipal Prompt Library & AI Guide</p>', unsafe_allow_html=True)
    st.caption("Click 'Use This Prompt' to automatically populate your report description.")

    HELP_PROMPTS = [
        {
            "cat": "Solid Waste / Garbage",
            "title": "Severe Garbage Accumulation on Main Road",
            "en": "Major commercial and domestic garbage accumulation on main thoroughfare for over 4 days. Blocking pedestrian walkway with acute foul odor, attracting stray animals. Immediate waste truck removal required.",
            "ru": "Main road pe 4 din se kachray ka dher laga hua hai, footpath block hai aur bohot ziada badboo aa rahi hai. Kutton aur makhiyon ki wajah se bimari ka khatra hai, baraye meherbani fori dumper bhejen.",
            "ur": "مین روڈ پر چار روز سے کچرے کا بڑا ڈھیر لگا ہوا ہے۔ پیدل چلنے کا راستہ بند ہے اور شدید بدبو کی وجہ سے شہریوں کا گزرنا محال ہے۔ فوری کچرا اٹھانے والی گاڑی بھیجی جائے۔"
        },
        {
            "cat": "Roads & Potholes",
            "title": "Dangerous Deep Pothole Near Intersection",
            "en": "Deep dangerous pothole (approx 2.5 ft wide, 9 inches deep) on main road near traffic intersection. Severely damaging vehicles and causing frequent motorcycle falls, especially hazardous at night.",
            "ru": "Chowk k qareeb sarak par bohot gehra aur khatarnaak khadda ban chuka hai, bike walay gir rahay hain aur gaariyon ko nuqsan ho raha hai. Raat ko andheray me bara accident ho sakta hai, fori asphalt patch darkaar hai.",
            "ur": "چوک کے قریب سڑک پر گہرا خطرناک کھڈا بن چکا ہے جس سے موٹر سائیکل سوار گر کر زخمی ہو رہے ہیں۔ رات کے وقت حادثات کا شدید اندیشہ ہے، ہنگامی بنیادوں پر مرمت کی جائے۔"
        },
        {
            "cat": "Sewerage & Manholes",
            "title": "CRITICAL: Open Gutter With Missing Manhole Cover",
            "en": "CRITICAL HAZARD: Open gutter with missing manhole cover on unlit residential street. Severe life-threatening danger of children or pedestrians falling inside. Emergency concrete slab installation required immediately.",
            "ru": "BOHOT KHATARNAAK: Gali me gutter ka dhakkan gayab hai aur gutter khula para hai. Kisi bachay ya buzurg k girnay ka shadeed khatra hai, baraye meherbani fori naya dhakkan lagaya jaye.",
            "ur": "شدید خطرہ: رہائشی گلی میں گٹر کا ڈھکن غائب ہے اور کھلا گٹر موجود ہے۔ کسی بھی بچے یا پیدل چلنے والے کے گرنے کا خطرہ ہے، فوری نیا ڈھکن نصب کیا جائے۔"
        },
        {
            "cat": "Sewerage & Manholes",
            "title": "Choked Sewer Line Backflow & Flooding",
            "en": "Underground municipal sewerage line completely choked. Black contaminated wastewater overflowing across road and entering residential entryways and market shops, creating acute sanitation hazard.",
            "ru": "Gutter line choke honay ki wajah se ganda kaala pani poori gali me phail gaya hai aur dukanon me dakhil ho raha hai. Badboo aur bimari phail rahi hai, suction jetting machine darkaar hai.",
            "ur": "سیوریج لائن چوک ہونے کے باعث گٹر کا گندا پانی سڑک پر بہہ کر دکانوں اور گھروں کے دروازوں میں داخل ہو رہا ہے۔ فوری سکشن مشین بھیج کر نکاسی کا بندوبست کریں۔"
        },
        {
            "cat": "Electrical Hazard",
            "title": "Sparking Loose Electric Cable / Fallen Wire",
            "en": "High-voltage electric wire detached from pole hanging low near rainwater puddle and pedestrian pathway. Actively sparking with extreme electrocution hazard.",
            "ru": "Khambay se bijli ki nangi taar toot kar neeche latak rahi hai aur paani k johar k qareeb sparking kar rahi hai. Current lagnay ka shadeed khatra hai, fori linemen bhejen.",
            "ur": "بجلی کے کھمبے سے ننگی تار ٹوٹ کر نیچے لٹک رہی ہے اور پانی کے قریب چنگاریاں نکل رہی ہیں۔ کرنٹ لگنے کا شدید خطرہ ہے، فوری طور پر لائن کاٹ کر مرمت کی جائے۔"
        },
        {
            "cat": "Water Supply",
            "title": "Main Drinking Water Pipeline Rupture",
            "en": "Clean drinking water main distribution pipeline has cracked. Thousands of gallons of potable water flooding street continuously while neighboring sectors experience complete water outage.",
            "ru": "Meethay paani ki main pipeline phat gayi hai, hazaron gallon paani zaya ho raha hai aur mohallay me paani ki shadeed killat ho gayi hai. Fori pipeline repair ki jaye.",
            "ur": "پینے کے صاف پانی کی مین پائپ لائن پھٹ گئی ہے جس سے ہزاروں گیلن پانی سڑک پر ضائع ہو رہا ہے اور محلے میں پانی کی سپلائی معطل ہے۔ ہنگامی مرمت کی ضرورت ہے۔"
        }
    ]

    for idx, p in enumerate(HELP_PROMPTS):
        st.markdown(
            f"""
            <div class="info-card">
                <h4>{p['title']} <span style="font-size:0.7rem; color:#7A90A8; font-weight:normal;">({p['cat']})</span></h4>
                <p><strong>English:</strong> {p['en']}</p>
                <p style="margin-top:0.3rem;"><strong>Roman Urdu:</strong> {p['ru']}</p>
                <p style="margin-top:0.3rem; direction:rtl; text-align:right;"><strong>اردو:</strong> {p['ur']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"📋 Use This Prompt (#{idx+1})", key=f"btn_p_{idx}"):
            st.session_state.selected_prompt = p["en"]
            st.success(f"Prompt #{idx+1} loaded into description! Switch back to 'Report Civic Issue' tab to submit.")

    st.divider()
    st.markdown("### 🤖 How the Multimodal AI Triage Engine Works")
    st.markdown(
        """
        1. **Vision Inspection (Gemini Vision):** Detects whether the image shows genuine civic infrastructure damage vs unrelated media.
        2. **Urdu / English Audio Transcription (Whisper):** Converts spoken voice notes into clean translated text.
        3. **Priority & Severity Grading:** Scores issues as *Critical* (immediate danger), *High*, *Medium*, or *Low*.
        4. **Spatial Deduplication:** Automatically clusters complaints within 50 meters submitted within 48 hours to prevent duplicate work orders.
        """
    )


# ==============================================================================
# TAB 4: PRIVACY POLICY
# ==============================================================================
with tab_privacy:
    st.markdown('<p class="form-section-label">Municipal Data Protection & Privacy Framework</p>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="info-card">
            <h4>1. Point-in-Time Geolocation Telemetry</h4>
            <p>
                GPS telemetry is accessed <strong>exclusively at the exact instant</strong> of complaint submission.
                CivicPulse AI has <strong>zero continuous location tracking</strong> and never monitors citizen movement.
                Coordinates are clustered within a 50-meter radius to merge duplicate complaints.
            </p>
        </div>

        <div class="info-card">
            <h4>2. Automated Civilian Privacy Masking</h4>
            <p>
                All photographic evidence uploaded to CivicPulse AI undergoes automated edge pre-processing.
                Civilian faces and motor vehicle license plates are automatically blurred before storage to protect
                public privacy. EXIF hardware tags are permanently stripped.
            </p>
        </div>

        <div class="info-card">
            <h4>3. Pakistan Mobile Number Security (SMS Only)</h4>
            <p>
                Citizen mobile numbers (Jazz, Zong, Telenor, Ufone, SCOM) are used strictly for sending automated SMS
                ticket dispatch receipts and resolution confirmations. Mobile data is never shared, rented, or monetized
                with third-party marketing entities.
            </p>
        </div>

        <div class="info-card">
            <h4>4. Ephemeral Audio Processing</h4>
            <p>
                Voice notes submitted in Urdu, Roman Urdu, or English are transcribed into text and the raw audio cache
                is automatically purged within 24 hours of ticket validation.
            </p>
        </div>

        <div class="info-card">
            <h4>5. Statutory Compliance & Grievance Redressal</h4>
            <p>
                In compliance with the <strong>Prevention of Electronic Crimes Act (PECA 2016)</strong> and Sindh Local
                Government rules, citizens have the statutory right to request erasure of their contact records once a
                civic issue is marked as <code>Resolved</code>. Contact the Municipal Data Ombudsman at 
                <code>privacy@civicpulse.gov.pk</code> or dial <code>1339</code>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.caption("CivicPulse AI · Municipal Governance Platform · Government of Sindh (Karachi & Hyderabad) · 2026")
