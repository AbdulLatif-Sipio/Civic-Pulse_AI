"""
CivicPulse AI — Help Center & AI Civic Prompt Library
Provides citizens with pre-calibrated civic prompts in English, Roman Urdu,
and Urdu to ensure maximum AI classification accuracy and rapid crew dispatch.
"""

import streamlit as st

st.set_page_config(
    page_title="CivicPulse AI — Help & Prompt Center",
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

    .help-badge {
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
    .help-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        margin: 0 0 0.5rem 0;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }
    .help-subtitle {
        font-size: 0.95rem;
        color: #475569;
        line-height: 1.6;
        margin-bottom: 2rem;
    }
    .prompt-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.3rem;
        margin-bottom: 1.3rem;
    }
    .prompt-category {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #15803D;
        margin-bottom: 0.4rem;
    }
    .prompt-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.6rem;
    }
    .lang-row {
        background: #FFFFFF;
        border-radius: 6px;
        padding: 0.7rem 0.9rem;
        margin-bottom: 0.5rem;
        border: 1px solid #E2E8F0;
        border-left: 3px solid #16A34A;
    }
    .lang-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    .lang-text {
        font-size: 0.9rem;
        color: #1E293B;
        line-height: 1.55;
        margin: 0;
    }
    .urdu-text {
        font-size: 1rem;
        direction: rtl;
        text-align: right;
        color: #0F172A;
        font-family: system-ui, -apple-system, sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="help-badge">Citizen Knowledge Base · AI Assistant</div>', unsafe_allow_html=True)
st.markdown('<h1 class="help-title">Help Center & Prompt Guide</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="help-subtitle">'
    'To help our Multimodal AI understand your report with high precision, use these field-tested '
    'prompts in English, Roman Urdu, or Urdu. The AI analyzes your text, audio recording, and photo '
    'to categorize the issue and assign priority.'
    '</p>',
    unsafe_allow_html=True,
)

st.markdown("### 📋 Frequently Reported Civic Issues")

category_filter = st.selectbox(
    "Filter by Hazard Category",
    options=["All Categories", "🗑️ Solid Waste / Garbage", "🕳️ Roads & Potholes", "🚰 Sewerage & Manholes", "⚡ Electrical Hazards", "💧 Water Supply Pipeline"]
)

PROMPTS = [
    {
        "cat": "🗑️ Solid Waste / Garbage",
        "title": "Severe Garbage Accumulation on Main Road",
        "en": "Major commercial and domestic garbage accumulation on main thoroughfare for over 4 days. Blocking pedestrian walkway with acute foul odor, attracting stray dogs and flies. Immediate dumper truck removal required.",
        "ru": "Main road pe 4 din se kachray ka dher laga hua hai, footpath block hai aur bohot ziada badboo aa rahi hai. Kutton aur makhiyon ki wajah se bimari ka khatra hai, baraye meherbani fori dumper bhejen.",
        "ur": "مین روڈ پر چار روز سے کچرے کا بڑا ڈھیر لگا ہوا ہے۔ پیدل چلنے کا راستہ بند ہے اور شدید بدبو کی وجہ سے شہریوں کا گزرنا محال ہے۔ فوری کچرا اٹھانے والی گاڑی بھیجی جائے۔"
    },
    {
        "cat": "🕳️ Roads & Potholes",
        "title": "Dangerous Deep Pothole Near Intersection",
        "en": "Deep dangerous pothole (approx 2.5 ft wide, 9 inches deep) on main road near traffic intersection. Severely damaging vehicles and causing frequent motorcycle falls, especially hazardous at night due to poor lighting.",
        "ru": "Chowk k qareeb sarak par bohot gehra aur khatarnaak khadda ban chuka hai, bike walay gir rahay hain aur gaariyon ko nuqsan ho raha hai. Raat ko andheray me bara accident ho sakta hai, fori asphalt patch lagaya jaye.",
        "ur": "چوک کے قریب سڑک پر گہرا خطرناک کھڈا بن چکا ہے جس سے موٹر سائیکل سوار گر کر زخمی ہو رہے ہیں۔ رات کے وقت حادثات کا شدید اندیشہ ہے، ہنگامی بنیادوں پر مرمت کی جائے۔"
    },
    {
        "cat": "🚰 Sewerage & Manholes",
        "title": "Life-Threatening Missing Manhole Cover",
        "en": "CRITICAL HAZARD: Open gutter with missing manhole cover on unlit residential street. Severe life-threatening danger of children or pedestrians falling inside. Emergency concrete slab installation required immediately.",
        "ru": "BOHOT KHATARNAAK: Gali me gutter ka dhakkan gayab hai aur gutter khula para hai. Kisi bachay ya buzurg k girnay ka shadeed khatra hai, baraye meherbani fori naya dhakkan lagaya jaye.",
        "ur": "شدید خطرہ: رہائشی گلی میں گٹر کا ڈھکن غائب ہے اور کھلا گٹر موجود ہے۔ کسی بھی بچے یا پیدل چلنے والے کے گرنے کا خطرہ ہے، فوری نیا ڈھکن نصب کیا جائے۔"
    },
    {
        "cat": "🚰 Sewerage & Manholes",
        "title": "Choked Sewer Line Backflow & Flooding",
        "en": "Underground municipal sewerage line completely choked. Black contaminated wastewater overflowing across road and entering residential entryways and market shops, creating acute sanitation hazard.",
        "ru": "Gutter line choke honay ki wajah se ganda kaala pani poori gali me phail gaya hai aur dukanon me dakhil ho raha hai. Badboo aur bimari phail rahi hai, suction jetting machine darkaar hai.",
        "ur": "سیوریج لائن چوک ہونے کے باعث گٹر کا گندا پانی سڑک پر بہہ کر دکانوں اور گھروں کے دروازوں میں داخل ہو رہا ہے۔ فوری سکشن مشین بھیج کر نکاسی کا بندوبست کریں۔"
    },
    {
        "cat": "⚡ Electrical Hazards",
        "title": "Sparking Loose Electric Wire / Fallen Cable",
        "en": "High-voltage electric wire detached from pole hanging low near rainwater puddle and pedestrian pathway. Actively sparking with extreme electrocution hazard.",
        "ru": "Khambay se bijli ki nangi taar toot kar neeche latak rahi hai aur paani k johar k qareeb sparking kar rahi hai. Current lagnay ka shadeed khatra hai, fori linemen bhejen.",
        "ur": "بجلی کے کھمبے سے ننگی تار ٹوٹ کر نیچے لٹک رہی ہے اور پانی کے قریب چنگاریاں نکل رہی ہیں۔ کرنٹ لگنے کا شدید خطرہ ہے، فوری طور پر لائن کاٹ کر مرمت کی جائے۔"
    },
    {
        "cat": "💧 Water Supply Pipeline",
        "title": "Main Drinking Water Pipeline Burst",
        "en": "Clean drinking water main distribution pipeline has cracked. Thousands of gallons of potable water flooding street continuously while neighboring sectors experience complete water outage.",
        "ru": "Meethay paani ki main pipeline phat gayi hai, hazaron gallon paani zaya ho raha hai aur mohallay me paani ki shadeed killat ho gayi hai. Fori pipeline repair ki jaye.",
        "ur": "پینے کے صاف پانی کی مین پائپ لائن پھٹ گئی ہے جس سے ہزاروں گیلن پانی سڑک پر ضائع ہو رہا ہے اور محلے میں پانی کی سپلائی معطل ہے۔ ہنگامی مرمت کی ضرورت ہے۔"
    }
]

for p in PROMPTS:
    if category_filter == "All Categories" or category_filter == p["cat"]:
        st.markdown(
            f"""
            <div class="prompt-box">
                <div class="prompt-category">{p['cat']}</div>
                <div class="prompt-title">{p['title']}</div>
                <div class="lang-row">
                    <div class="lang-label">English (Municipal Standard)</div>
                    <p class="lang-text">{p['en']}</p>
                </div>
                <div class="lang-row">
                    <div class="lang-label">Roman Urdu (Common Spoken)</div>
                    <p class="lang-text">{p['ru']}</p>
                </div>
                <div class="lang-row">
                    <div class="lang-label">Urdu Script (اردو)</div>
                    <p class="lang-text urdu-text">{p['ur']}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

st.markdown("### 📸 Best Practices for Submission")
col_photo, col_voice = st.columns(2)

with col_photo:
    st.markdown(
        """
        **Photographs:**
        - Take photos during daylight or with flash.
        - Step back 6-10 feet to capture landmark context (shops, signs, street number).
        - Ensure problem area (pothole edge, garbage depth) is in sharp focus.
        """
    )

with col_voice:
    st.markdown(
        """
        **Voice Notes:**
        - State the specific street or chowk name clearly.
        - Mention duration (e.g. *'ye masla 3 din se hai'*).
        - State immediate hazards (e.g. *'school k samnay hai, bachay gir rahay hain'*).
        """
    )

st.divider()
st.caption("CivicPulse AI · Citizen Knowledge Base · Government of Sindh Municipal Services")
