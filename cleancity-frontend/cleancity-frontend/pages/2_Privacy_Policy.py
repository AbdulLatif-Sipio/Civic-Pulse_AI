"""
CivicPulse AI — Municipal Data Protection & Privacy Framework
Statutory Compliance: Prevention of Electronic Crimes Act (PECA 2016),
Sindh Local Government Act 2013, and Personal Data Protection Principles.
"""

import streamlit as st

st.set_page_config(
    page_title="CivicPulse AI — Privacy & Citizen Data Policy",
    page_icon=None,
    layout="centered",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

    /* ── Clean Municipal Light Theme ── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }
    .main .block-container {
        max-width: 780px;
        padding: 2.5rem 2rem 4rem 2rem;
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
        margin-top: 1.5rem;
        margin-bottom: 2rem;
    }

    /* ── Hide Streamlit Branding & Toolbar ── */
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

    .legal-badge {
        display: inline-block;
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.3rem 0.75rem;
        margin-bottom: 0.75rem;
    }
    .policy-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        margin: 0 0 0.5rem 0;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    .policy-subtitle {
        font-size: 0.95rem;
        color: #475569;
        line-height: 1.6;
        margin-bottom: 2rem;
    }
    .policy-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.4rem;
        margin-bottom: 1.4rem;
    }
    .policy-card h3 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #15803D;
        font-size: 1.12rem;
        font-weight: 700;
        margin-top: 0;
        margin-bottom: 0.75rem;
    }
    .policy-card p, .policy-card li {
        color: #334155;
        font-size: 0.9rem;
        line-height: 1.65;
    }
    .highlight-pill {
        background: #F1F5F9;
        color: #0F172A;
        border: 1px solid #CBD5E1;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
        font-size: 0.82rem;
        font-family: monospace;
    }
    hr {
        border-color: #E2E8F0 !important;
        margin: 2rem 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="legal-badge">Official Municipal Framework · Government of Sindh</div>', unsafe_allow_html=True)
st.markdown('<h1 class="policy-title">Privacy & Citizen Data Policy</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="policy-subtitle">'
    'CivicPulse AI is committed to safeguarding citizen privacy under the '
    '<strong>Prevention of Electronic Crimes Act (PECA 2016)</strong>, Sindh Local Government Act, '
    'and international municipal open-data governance standards. This charter details how your photographic, '
    'spatial, voice, and telephony data are processed and protected.'
    '</p>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="policy-card">
        <h3>1. Point-in-Time Geolocation Telemetry (No Background Tracking)</h3>
        <p>
            CivicPulse AI accesses device GPS coordinates <strong>exclusively at the exact instant</strong> 
            a citizen submits an infrastructure report.
        </p>
        <ul>
            <li><strong>Zero Continuous Tracking:</strong> The application does not monitor your movement, track commuting routes, or retain location breadcrumbs.</li>
            <li><strong>Spatial Clustered Deduplication:</strong> Coordinates are hashed and matched within a <strong>50-meter radius</strong> to group redundant complaints without revealing personal identity.</li>
            <li><strong>Citizen Coordinate Control:</strong> Users can manually select predefined municipal ward landmarks (e.g. Saddar, Clifton, Autobahn Road) if they decline device GPS permissions.</li>
        </ul>
    </div>

    <div class="policy-card">
        <h3>2. Photographic Evidence & Automated Civilian Anonymization</h3>
        <p>
            Photographs submitted as evidence of municipal failure (garbage heaps, road craters, sewer bursts) 
            are processed through automated Computer Vision filtering:
        </p>
        <ul>
            <li><strong>Visual Anonymization:</strong> Civilian faces and motor vehicle license registration plates captured in submitted frames are automatically blurred by edge pre-processing.</li>
            <li><strong>Metadata Scrubbing:</strong> Embedded EXIF metadata (camera serials, device hardware IDs) is removed upon receipt by municipal ingestion nodes.</li>
            <li><strong>Protected Local Storage:</strong> Images are stored on encrypted municipal government servers with role-based cryptographic authorization.</li>
        </ul>
    </div>

    <div class="policy-card">
        <h3>3. Telephony & Pakistan Mobile Number (SMS Notification Only)</h3>
        <p>
            Citizens can provide their Pakistan cellular mobile number (Jazz, Zong, Telenor, Ufone, SCOM) 
            to receive official municipal status notifications.
        </p>
        <ul>
            <li><strong>Strict Purpose Limitation:</strong> Your mobile number is used <em>solely</em> to dispatch automated SMS updates regarding your ticket tracking reference (e.g. <code>TKT-A8F12C</code>) and field crew dispatch alerts.</li>
            <li><strong>Zero Commercial Monetization:</strong> Citizen contact details are never shared, leased, or disclosed to advertising networks, commercial entities, or non-municipal third parties.</li>
            <li><strong>Optional Submission:</strong> Submitting a mobile number is completely voluntary and is not mandatory to report civic hazards.</li>
        </ul>
    </div>

    <div class="policy-card">
        <h3>4. Voice Telemetry & Ephemeral Transcription</h3>
        <p>
            Voice notes recorded in Urdu, Roman Urdu, Sindhi, or English are processed through on-premise 
            AI transcription engines:
        </p>
        <ul>
            <li><strong>Ephemeral Voice Buffer:</strong> Audio recordings are transcribed into textual descriptions and the temporary audio buffer is purged within 24 hours of ticket validation.</li>
            <li><strong>No Voice Biometric Profiling:</strong> CivicPulse AI does not create voice biometric prints or speaker identification models.</li>
        </ul>
    </div>

    <div class="policy-card">
        <h3>5. Citizen Grievance Redressal & Right to Erasure</h3>
        <p>
            Under Section 45 of PECA 2016 and provincial data governance directives, any citizen has the statutory right to:
        </p>
        <ul>
            <li>Request inspection of records linked to their mobile number or ticket references.</li>
            <li>Request immediate redaction or deletion of their contact records once a municipal complaint is marked as <code>Resolved</code>.</li>
            <li>Contact the <strong>Municipal Data Protection & Ombudsman Office</strong>: <code>privacy@civicpulse.gov.pk</code> or call the Citizen Grievance Helpline at <code>1339</code>.</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()
st.caption("CivicPulse AI · Government of Sindh Municipal Services · Data Protection Officer (DPO) Reg: PK-SND-2026-CC")
