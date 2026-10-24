"""
CivicPulse AI — Terms of Service & Municipal Portal Conditions
Statutory Framework: Sindh Local Government Act 2013,
Prevention of Electronic Crimes Act (PECA 2016), and Municipal Redressal Regulations.
"""

import streamlit as st

st.set_page_config(
    page_title="CivicPulse AI — Terms and Conditions",
    page_icon="⚖️",
    layout="centered",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

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
        background: #EFF6FF;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 0.25rem 0.6rem;
        margin-bottom: 0.6rem;
    }
    .legal-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #0F172A;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    .legal-meta {
        font-size: 0.85rem;
        color: #475569;
        margin-bottom: 2rem;
        padding-bottom: 1.2rem;
        border-bottom: 1px solid #E2E8F0;
    }
    .legal-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
    }
    .legal-card h4 {
        color: #1E40AF;
        margin: 0 0 0.4rem 0;
        font-size: 1rem;
        font-weight: 700;
    }
    .legal-card p {
        color: #334155;
        font-size: 0.88rem;
        margin: 0;
        line-height: 1.6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<span class="legal-badge">Statutory Governance Regulations</span>', unsafe_allow_html=True)
st.markdown('<h1 class="legal-title">Terms & Conditions of Service</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="legal-meta">'
    'Effective Date: <strong>1st January 2026</strong> &nbsp;|&nbsp; '
    'Jurisdiction: <strong>Government of Sindh (Karachi & Hyderabad)</strong> &nbsp;|&nbsp; '
    'Compliance: <strong>PECA 2016 & SLGA 2013</strong>'
    '</p>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="legal-card">
        <h4>1. Purpose and Civic Scope</h4>
        <p>
            CivicPulse AI provides an AI-augmented municipal routing gateway for citizens of Karachi Metropolitan
            Corporation (KMC) and Hyderabad Municipal Corporation (HMC). By submitting photographic or audio evidence,
            citizens consent to automated machine triage, geospatial clustering, and operational dispatch to municipal
            field maintenance departments.
        </p>
    </div>

    <div class="legal-card">
        <h4>2. Permitted Reporting & Truthfulness Obligations</h4>
        <p>
            Submissions must represent genuine, active public infrastructure concerns (e.g. solid waste accumulation,
            sewer overflow, open manholes, hazardous potholes, detached electrical cables, or broken water supply mains).
            Deliberate falsification, hoax emergency alerts, commercial advertisements, or abusive content is strictly
            prohibited and subject to prosecution under Section 14 of the Prevention of Electronic Crimes Act (PECA 2016).
        </p>
    </div>

    <div class="legal-card">
        <h4>3. AI Triage & Municipal SLAs</h4>
        <p>
            CivicPulse AI employs multimodal vision models and geospatial algorithms to assign initial severity ratings
            (<em>Critical</em>, <em>High</em>, <em>Medium</em>, <em>Low</em>) and generate action plans. While critical
            hazards trigger immediate priority supervisor email dispatches, response times depend on field crew availability,
            zonal resource allocations, and weather conditions. Registration does not constitute a legally binding guarantee
            of immediate completion.
        </p>
    </div>

    <div class="legal-card">
        <h4>4. Evidence Ownership & Public Interest License</h4>
        <p>
            Citizens retain copyright of photographic and audio media submitted through the portal, while granting the
            Government of Sindh and affiliated municipal bodies a non-exclusive, perpetual, royalty-free license to use,
            display, blur civilian identifiers, and analyze such evidence for municipal inspection and resolution tracking.
        </p>
    </div>

    <div class="legal-card">
        <h4>5. Anti-Spam & Automated Bot Prevention</h4>
        <p>
            Automated crawling, rapid script submissions, denial-of-service attempts, or bypassing rate limits (15 requests/min)
            is strictly monitored. Offending IP addresses and devices will be permanently blocked from municipal service networks.
        </p>
    </div>

    <div class="legal-card">
        <h4>6. Grievance Appeals & Ombudsman Inquiries</h4>
        <p>
            For questions regarding ticket resolution disputes, service terms, or data policies, citizens may contact the
            Provincial Municipal Ombudsman at <code>legal@civicpulse.sindh.gov.pk</code> or call the helpline at <code>1339</code>.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    if st.button("⬅️ Return to Citizen Portal", type="primary"):
        st.switch_page("app.py")
with col_nav2:
    if st.button("🔒 View Privacy Policy", type="secondary"):
        st.switch_page("pages/2_Privacy_Policy.py")
