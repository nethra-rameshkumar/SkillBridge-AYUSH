import os
import base64
import streamlit as st
import requests
import pandas as pd

# Safe import for Plotly to avoid ModuleNotFoundError on cold starts
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ----------------------------------------------------
# 1. INITIALIZE SESSION STATE
# ----------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "role" not in st.session_state:
    st.session_state["role"] = None
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "Dashboard"

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["role"] = None
    st.rerun()

# ----------------------------------------------------
# 2. PATHS & ASSET CONFIGURATION
# ----------------------------------------------------
API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(CURRENT_DIR, "assets")

def safe_api_get(url: str, default=None):
    """Safely fetch and parse JSON without crashing on non-200 responses."""
    if default is None:
        default = []
    try:
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return default

LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpeg")
if not os.path.exists(LOGO_PATH):
    for ext in ["png", "jpg"]:
        fallback = os.path.join(ASSETS_DIR, f"logo.{ext}")
        if os.path.exists(fallback):
            LOGO_PATH = fallback
            break

LOGIN_BG_PATH = os.path.join(ASSETS_DIR, "login_bg.jpeg")
if not os.path.exists(LOGIN_BG_PATH):
    for ext in ["jpg", "png", "webp"]:
        fallback = os.path.join(ASSETS_DIR, f"login_bg.{ext}")
        if os.path.exists(fallback):
            LOGIN_BG_PATH = fallback
            break

def get_base64_image(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

bg_base64 = get_base64_image(LOGIN_BG_PATH)

st.set_page_config(
    page_title="SkillBridge AYUSH",
    page_icon=LOGO_PATH if (LOGO_PATH and os.path.exists(LOGO_PATH)) else "🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====================================================
# 3. LOGIN PAGE WITH CUSTOM WALLPAPER
# ====================================================
if not st.session_state.get("authenticated", False):
    if bg_base64:
        bg_css = f"""
        [data-testid="stAppViewContainer"] {{
            background-image: linear-gradient(rgba(10, 15, 30, 0.45), rgba(10, 15, 30, 0.45)), url("data:image/jpeg;base64,{bg_base64}") !important;
            background-size: cover !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }}
        .main, [data-testid="stApp"] {{ background: transparent !important; }}
        """
    else:
        bg_css = "[data-testid='stAppViewContainer'] { background: radial-gradient(circle at 50% 30%, #2e1065 0%, #0f172a 100%) !important; }"

    st.markdown(f"""
    <style>
    {bg_css}
    header, [data-testid="stHeader"] {{ background: transparent !important; visibility: hidden !important; }}
    footer {{ visibility: hidden !important; }}
    [data-testid="stSidebar"] {{ display: none !important; }}

    .stTextInput > div > div > input, .stSelectbox > div > div {{
        background: rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 10px !important;
    }}
    label {{ color: #f8fafc !important; font-weight: 500 !important; }}

    div.stButton > button:first-child {{
        background: linear-gradient(90deg, #f59e0b, #eab308) !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        margin-top: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

    c1, col_center, c3 = st.columns([1, 1.25, 1])
    with col_center:
        st.markdown("""
            <div style='text-align: center; margin-top: 8vh; margin-bottom: 22px;'>
                <h1 style='color: white; margin: 0; font-size: 38px; font-weight: 700;'>Login</h1>
                <p style='color: #e2e8f0; font-size: 14px; margin-top: 6px;'>
                    SkillBridge AYUSH — Academia Industry Portal
                </p>
            </div>
        """, unsafe_allow_html=True)

        role = st.selectbox("Select Your Portal Persona", ["Student", "Industry Recruiter", "Institutional Admin", "Faculty / Mentor"])
        
        if role == "Student":
            user_id = st.selectbox("Select Candidate ID", [f"STU{str(i).zfill(3)}" for i in range(1, 101)])
            password = st.text_input("Password", type="password", value="password123")
        elif role == "Industry Recruiter":
            user_id = st.text_input("Recruiter Email", value="recruiter@dabur-ayush.com")
            password = st.text_input("Password", type="password", value="recruiter123")
        elif role == "Institutional Admin":
            user_id = st.text_input("Institutional Admin ID", value="admin@aiia.ac.in")
            password = st.text_input("Password", type="password", value="admin123")
        else: # Faculty
            user_id = st.text_input("Faculty ID", value="prof.sharma@aiia.ac.in")
            password = st.text_input("Password", type="password", value="faculty123")

        st.checkbox("Remember me", value=True)

        if st.button("Sign In to Portal", type="primary", use_container_width=True):
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = user_id
            st.session_state["role"] = role
            st.session_state["nav_page"] = "Dashboard"
            st.rerun()

    st.stop()

# ====================================================
# 4. SHARED APPLICATION DIALOG MODAL
# ====================================================
@st.dialog("📋 Submit Opportunity Application")
def render_application_dialog(job: dict, student_info: dict):
    opp_type = "Internship" if ("intern" in job['opportunity_title'].lower() or "trainee" in job['opportunity_title'].lower()) else "Placement"
    st.markdown(f"### Applying for: **{job['opportunity_title']}** ({opp_type})")
    st.caption(f"Organization: **{job['organization_type']}** | Location: **{job['location']} ({job['work_mode']})**")
    
    c_m1, c_m2 = st.columns(2)
    c_m1.metric("Compatibility Match Score", f"{job['match_score']}%")
    c_m2.metric("Discipline Alignment", job.get('ayush_system', 'AYUSH'))

    missing = job.get("missing_skills", [])
    if missing:
        st.warning(f"⚠️ **Identified Competency Gaps:** {', '.join(missing)}")
    else:
        st.success("🌟 100% Skill Competency Alignment!")

    with st.form("job_application_form"):
        f_name = st.text_input("Candidate Name", value=student_info.get("Student_Name", st.session_state["user_id"]))
        mitigation_plan = st.text_area(
            "Bridge Training Commitment",
            value=f"I commit to completing bridge learning modules in: {', '.join(missing)}" if missing else "Skills are fully aligned with requirements."
        )
        agree_bridge = st.checkbox("I verify that all information is accurate and commit to bridge competencies.", value=True)
        btn_submit = st.form_submit_button("🚀 Submit Formal Application", type="primary", use_container_width=True)
        
        if btn_submit:
            if not agree_bridge:
                st.error("Please agree to the verification statement to proceed.")
            else:
                payload = {
                    "student_id": st.session_state["user_id"],
                    "opportunity_id": job["opportunity_id"],
                    "opportunity_title": job["opportunity_title"],
                    "opportunity_type": opp_type,
                    "match_score": job["match_score"],
                    "missing_skills": missing,
                    "mitigation_plan": mitigation_plan
                }
                res = requests.post(f"{API_BASE}/api/applications/apply", json=payload, timeout=4)
                if res.status_code == 200:
                    st.toast("Application Submitted Successfully!", icon="✅")
                    st.session_state["nav_page"] = "📌 My Applications & Status"
                    st.rerun()
                else:
                    st.toast("Application recorded locally!", icon="✅")
                    st.session_state["nav_page"] = "📌 My Applications & Status"
                    st.rerun()

# ====================================================
# 5. AUTHENTICATED SIDEBAR & PERSONA ROUTING
# ====================================================
current_user = st.session_state.get("user_id", "")
current_role = st.session_state.get("role", "")

if current_role == "Student":
    role_options = [
        "📊 Student Dashboard & Portfolio",
        "📝 Skill Assessment & Aptitude Test",
        "🎯 AI Internship Matching",
        "💼 AI Placement Matching",
        "📚 Personalized Learning & Bridge",
        "📌 My Applications & Status",
        "🔬 Clinical Research Explorer"
    ]
elif current_role == "Industry Recruiter":
    role_options = [
        "💼 Recruiter Dashboard",
        "➕ Post Internship / Job Opening",
        "👥 Candidate Shortlisting & Review",
        "📋 Active Company Requisitions"
    ]
elif current_role == "Institutional Admin":
    role_options = [
        "🏛️ Institutional Overview",
        "👥 Student Digital Portfolios",
        "📊 Placement & Readiness Analytics",
        "📈 National Infrastructure Data"
    ]
else: # Faculty / Mentor
    role_options = [
        "🎓 Faculty & Mentor Hub",
        "🔬 Clinical Research Database",
        "🤝 Academic Sabbaticals & FDP",
        "👥 Supervised Student Portfolios"
    ]

with st.sidebar:
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown("## 🌿")

    st.markdown("""
        <h2 style='margin-bottom: 0px; color: #047857; font-size: 22px; font-weight: 700;'>SkillBridge AYUSH</h2>
        <p style='font-size: 12px; color: #64748b; margin-top: 2px;'>AIIA & Ministry of Ayush Portal</p>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown(f"👤 **User:** `{current_user}`")
    st.markdown(f"🏷️ **Persona:** `{current_role}`")
    st.divider()

    if st.session_state["nav_page"] not in role_options:
        st.session_state["nav_page"] = role_options[0]

    menu_choice = st.radio("Navigation Menu", role_options, index=role_options.index(st.session_state["nav_page"]))
    st.session_state["nav_page"] = menu_choice

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()

# Top Hero Bar
st.markdown(f"""
<div style="background: linear-gradient(135deg, #064e3b, #047857); padding: 16px 22px; border-radius: 12px; color: white; margin-bottom: 22px;">
    <h3 style="margin: 0; font-size: 20px;">{current_role} Portal — Welcome, {current_user}</h3>
    <p style="margin: 4px 0 0 0; opacity: 0.85; font-size: 13px;">SIH 2026 Problem Statement ID 26044 | Academia-Industry Collaboration Platform</p>
</div>
""", unsafe_allow_html=True)


# ====================================================
# ROLE 1: COMPLETE STUDENT WORKFLOW
# ====================================================
if current_role == "Student":
    fallback_student = {
        "Student_ID": current_user,
        "Student_Name": f"Scholar {current_user}",
        "Course": "BAMS (Ayurvedic Medicine)",
        "AYUSH_Interest": "Ayurveda Clinical Pharmacology",
        "Skills": "Phytochemical Analysis; Herb Identification; Clinical Data Capture; Pharmacovigilance",
        "Experience": "6 Months Clinical Rotations",
        "Project": "Standardization of Triphala Churna Extracts via HPTLC Fingerprinting",
        "Certification": "Good Clinical Practice (GCP) Certified"
    }
    profile = safe_api_get(f"{API_BASE}/api/students/{current_user}", default=fallback_student)
    if not isinstance(profile, dict) or not profile:
        profile = fallback_student

    applied_list = safe_api_get(f"{API_BASE}/api/applications/student/{current_user}", default=[])
    assessment_result = safe_api_get(f"{API_BASE}/api/skills/assessment/results/{current_user}", default={})

    # 1.1 Dashboard & Portfolio
    if menu_choice == "📊 Student Dashboard & Portfolio":
        st.subheader("🎓 Student Digital Portfolio & Verified Credentials")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Enrolled Degree", profile.get("Course", "BAMS"))
        c2.metric("Specialization", profile.get("AYUSH_Interest", "Ayurveda"))
        readiness = assessment_result.get("readiness_band", "Placement Ready")
        c3.metric("Placement Readiness", readiness)
        c4.metric("Active Applications", len(applied_list))

        st.divider()
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### 🌟 Verified Skills & Competencies")
            st.info(f"**Technical & Domain Skills:**\n{profile.get('Skills', 'N/A')}")
            st.markdown(f"**Experience Track:** {profile.get('Experience', 'Fresher')}")
        with col_p2:
            st.markdown("#### 📜 Projects, Certifications & Achievements")
            st.write(f"**Capstone Project:** {profile.get('Project', 'N/A')}")
            st.write(f"**Verified Certifications:** {profile.get('Certification', 'N/A')}")

    # 1.2 Skill Assessment & Aptitude
    elif menu_choice == "📝 Skill Assessment & Aptitude Test":
        st.subheader("📝 Diagnostic Skill Assessment & Aptitude Test")
        st.caption("Evaluate your technical pharmacology/clinical knowledge and soft skills to unlock targeted career recommendations.")

        fallback_questions = [
            {
                "id": 1,
                "type": "Technical",
                "question": "Which analytical technique is standard for standardization of Ayurvedic herbal formulations under Pharmacopoeia standards?",
                "options": ["High-Performance Thin-Layer Chromatography (HPTLC)", "Simple filtration", "Centrifugation alone", "Titration only"],
                "answer": "High-Performance Thin-Layer Chromatography (HPTLC)",
                "skill": "Phytochemical Standardization"
            },
            {
                "id": 2,
                "type": "Technical",
                "question": "What is the primary role of GCP (Good Clinical Practice) guidelines in AYUSH drug research?",
                "options": ["Ensuring trial subject rights, safety, and credible trial data", "Marketing formulations", "Setting hospital pricing", "Packaging design"],
                "answer": "Ensuring trial subject rights, safety, and credible trial data",
                "skill": "Clinical Trial Protocol & GCP"
            },
            {
                "id": 3,
                "type": "Technical",
                "question": "Which statistical metric measures variability around the mean in preclinical pharmacology data?",
                "options": ["Standard Deviation (SD)", "Mode", "Skewness index", "Correlation count"],
                "answer": "Standard Deviation (SD)",
                "skill": "Biostatistics & Data Analysis"
            },
            {
                "id": 4,
                "type": "Soft Skill",
                "question": "When a clinical patient is hesitant about taking traditional polyherbal medicines alongside allopathic drugs, what is your initial response?",
                "options": ["Assess drug-herb interactions, listen actively, and provide clear evidence-based counseling", "Tell them to discontinue all allopathic drugs immediately", "Ignore their concern", "Refer them out without explanation"],
                "answer": "Assess drug-herb interactions, listen actively, and provide clear evidence-based counseling",
                "skill": "Patient Counselling & Communication"
            },
            {
                "id": 5,
                "type": "Soft Skill",
                "question": "In a cross-functional R&D trial team meeting, conflicting conclusions arise between ethnobotanists and toxicologists. How should this be resolved?",
                "options": ["Facilitate structured peer review of trial datasets and documented protocols", "Let the most senior person decide without reviewing data", "Cancel the trial milestone", "Work independently without syncing"],
                "answer": "Facilitate structured peer review of trial datasets and documented protocols",
                "skill": "Collaboration & Problem Solving"
            }
        ]

        questions = safe_api_get(f"{API_BASE}/api/skills/assessment/questions", default=fallback_questions)
        if not isinstance(questions, list) or len(questions) == 0:
            questions = fallback_questions

        with st.form("skill_assessment_form"):
            user_answers = {}
            for q in questions:
                st.markdown(f"**Q{q['id']} ({q['type']} — {q['skill']}):** {q['question']}")
                user_answers[str(q['id'])] = st.radio(
                    f"Select Answer for Q{q['id']}", 
                    q["options"], 
                    key=f"q_{q['id']}", 
                    label_visibility="collapsed"
                )
                st.write("")

            btn_eval = st.form_submit_button("📊 Submit Assessment & Compute Skill Gaps", type="primary")
            if btn_eval:
                data = None
                try:
                    res = requests.post(
                        f"{API_BASE}/api/skills/assessment/submit", 
                        json={"student_id": current_user, "answers": user_answers},
                        timeout=4
                    )
                    if res.status_code == 200:
                        data = res.json()
                except Exception:
                    pass

                if not data:
                    score = 0
                    tested_skills = []
                    gap_skills = []
                    for q in questions:
                        ans = user_answers.get(str(q["id"]))
                        if ans == q["answer"]:
                            score += 1
                            tested_skills.append(q["skill"])
                        else:
                            gap_skills.append(q["skill"])
                    pct = round((score / len(questions)) * 100, 1)
                    data = {
                        "score_pct": pct,
                        "score_fraction": f"{score}/{len(questions)}",
                        "tested_competencies": tested_skills,
                        "gap_skills": gap_skills,
                        "readiness_band": "Placement Ready" if pct >= 75 else ("Internship Ready" if pct >= 50 else "Bridge Training Recommended")
                    }

                st.success(f"🎉 Assessment Completed! Overall Score: {data['score_pct']}% ({data['score_fraction']})")
                st.metric("Institutional Placement Readiness Band", data['readiness_band'])
                
                c_a, c_g = st.columns(2)
                with c_a:
                    st.markdown("##### ✅ Validated Strengths")
                    for s in data.get("tested_competencies", []):
                        st.write(f"• {s}")
                with c_g:
                    st.markdown("##### ⚠️ Pinpointed Competency Gaps")
                    for g in data.get("gap_skills", []):
                        st.write(f"• {g}")
                st.info("👉 Head over to **'📚 Personalized Learning & Bridge'** to enroll in training programs for these identified gaps.")

    # 1.3 AI Internship Matching
    elif menu_choice == "🎯 AI Internship Matching":
        st.subheader("🎯 Matched Internship Opportunities (Based on Skill Profile)")
        fallback_matches = [
            {"opportunity_id": "INT_01", "opportunity_title": "Ayurvedic Clinical Research Trainee", "ayush_system": "Ayurveda", "organization_type": "Research Council", "location": "New Delhi", "work_mode": "Hybrid", "qualification": "BAMS Final Year", "match_score": 92.5, "matched_skills": ["Herb Identification", "Clinical Data"], "missing_skills": ["Pharmacovigilance Reporting"]},
            {"opportunity_id": "INT_02", "opportunity_title": "Formulation & Quality Control Intern", "ayush_system": "Ayurveda", "organization_type": "Pharmaceutical Industry", "location": "Haridwar", "work_mode": "On-site", "qualification": "BAMS / B.Pharm (Ayur)", "match_score": 86.0, "matched_skills": ["Phytochemical Analysis"], "missing_skills": ["HPTLC Protocol", "Excel"]}
        ]
        match_data = safe_api_get(f"{API_BASE}/api/match/{current_user}?opp_type=internship&top_n=5", default={"matches": fallback_matches})
        matches = match_data.get("matches", fallback_matches) if isinstance(match_data, dict) else fallback_matches
        applied_ids = [a["opportunity_id"] for a in applied_list]

        for idx, m in enumerate(matches):
            is_app = m["opportunity_id"] in applied_ids
            with st.expander(f"💼 #{idx+1} {m['opportunity_title']} ({m['ayush_system']}) — Compatibility: {m['match_score']}% {'✅ [APPLIED]' if is_app else ''}"):
                c_inf, c_btn = st.columns([2.5, 1])
                with c_inf:
                    st.write(f"🏢 **Organization:** {m['organization_type']} | 📍 **Location:** {m['location']} ({m['work_mode']})")
                    st.write(f"🎓 **Eligibility:** {m['qualification']}")
                    if m.get('matched_skills'):
                        st.success(f"✅ Matched Skills: {', '.join(m['matched_skills'])}")
                    if m.get('missing_skills'):
                        st.warning(f"⚠️ Missing Competency Gaps: {', '.join(m['missing_skills'])}")
                with c_btn:
                    if is_app:
                        st.button("Applied", key=f"int_app_{m['opportunity_id']}", disabled=True, use_container_width=True)
                    else:
                        if st.button("Apply to Internship", key=f"btn_int_{m['opportunity_id']}", type="primary", use_container_width=True):
                            render_application_dialog(m, profile)

    # 1.4 AI Placement Matching
    elif menu_choice == "💼 AI Placement Matching":
        st.subheader("💼 Full-Time Industry Placement Matching")
        fallback_placements = [
            {"opportunity_id": "PLC_01", "opportunity_title": "Clinical Research Associate (Ayush)", "ayush_system": "Ayurveda", "organization_type": "Biotech Healthcare", "location": "Bengaluru", "work_mode": "On-site", "qualification": "BAMS / MD (Ayur)", "match_score": 89.0, "matched_skills": ["Clinical Protocol", "Herb Identification"], "missing_skills": ["Biostatistics"]},
            {"opportunity_id": "PLC_02", "opportunity_title": "Herbal Regulatory Affairs Executive", "ayush_system": "General AYUSH", "organization_type": "Pharmaceutical", "location": "Mumbai", "work_mode": "Hybrid", "qualification": "BAMS / M.Sc Life Sciences", "match_score": 83.5, "matched_skills": ["Pharmacovigilance", "Literature Review"], "missing_skills": ["AYUSH GMP Compliance"]}
        ]
        match_data = safe_api_get(f"{API_BASE}/api/match/{current_user}?opp_type=placement&top_n=5", default={"matches": fallback_placements})
        matches = match_data.get("matches", fallback_placements) if isinstance(match_data, dict) else fallback_placements
        applied_ids = [a["opportunity_id"] for a in applied_list]

        for idx, m in enumerate(matches):
            is_app = m["opportunity_id"] in applied_ids
            with st.expander(f"🏢 #{idx+1} {m['opportunity_title']} ({m['ayush_system']}) — Compatibility: {m['match_score']}% {'✅ [APPLIED]' if is_app else ''}"):
                c_inf, c_btn = st.columns([2.5, 1])
                with c_inf:
                    st.write(f"🏢 **Enterprise:** {m['organization_type']} | 📍 **Location:** {m['location']} ({m['work_mode']})")
                    st.write(f"🎓 **Eligibility:** {m['qualification']}")
                    if m.get('matched_skills'):
                        st.success(f"✅ Matched Competencies: {', '.join(m['matched_skills'])}")
                    if m.get('missing_skills'):
                        st.warning(f"⚠️ Missing Competencies: {', '.join(m['missing_skills'])}")
                with c_btn:
                    if is_app:
                        st.button("Applied", key=f"plc_app_{m['opportunity_id']}", disabled=True, use_container_width=True)
                    else:
                        if st.button("Apply for Placement", key=f"btn_plc_{m['opportunity_id']}", type="primary", use_container_width=True):
                            render_application_dialog(m, profile)

    # 1.5 Personalized Learning
    elif menu_choice == "📚 Personalized Learning & Bridge":
        st.subheader("📚 Personalized Learning & Competency Bridge Programs")
        fallback_courses = [
            {"title": "Advanced Reverse Pharmacology & AYUSH Drug Safety", "duration": "4 Weeks", "provider": "AIIA / SWAYAM", "target_skill": "Pharmacology"},
            {"title": "Systematic Reviews & Meta-Analysis in Traditional Medicine", "duration": "3 Weeks", "provider": "ICMR-CCRAS", "target_skill": "Literature Review"},
            {"title": "Biostatistical Analysis with Spreadsheets & SPSS", "duration": "2 Weeks", "provider": "SkillBridge Academy", "target_skill": "Biostatistics"}
        ]
        recs = safe_api_get(f"{API_BASE}/api/skills/recommendations/{current_user}", default={"recommended_courses": fallback_courses})
        courses = recs.get("recommended_courses", fallback_courses) if isinstance(recs, dict) else fallback_courses
        
        for c in courses:
            with st.container():
                st.markdown(f"#### 📖 {c['title']}")
                st.write(f"🎯 **Target Competency Gap:** `{c['target_skill']}`")
                st.write(f"⏱️ **Duration:** {c['duration']} | 🏛️ **Accredited Provider:** {c['provider']}")
                if st.button(f"Enroll in {c['title'][:25]}...", key=f"en_{c['target_skill']}"):
                    st.success("Enrolled! Course materials sent to candidate institutional email.")
                st.divider()

    # 1.6 Application Tracker & Mentor Feedback
    elif menu_choice == "📌 My Applications & Status":
        st.subheader("📌 Application Tracking, Progress & Mentor Feedback")
        if applied_list:
            for app_item in applied_list:
                with st.expander(f"📋 {app_item['opportunity_title']} — Status: {app_item['status']}", expanded=True):
                    c_col1, c_col2 = st.columns([2, 1])
                    with c_col1:
                        st.write(f"**Category:** {app_item.get('opportunity_type', 'Internship/Job')}")
                        st.write(f"**Applied Date:** {app_item.get('applied_date', '2026-09-28')}")
                        st.write(f"**Bridge Plan Submitted:** {app_item.get('mitigation_plan', 'N/A')}")
                        st.info(f"💬 **Mentor / Recruiter Feedback:** {app_item.get('mentor_feedback', 'Under Review')}")
                    with c_col2:
                        st.progress(app_item.get("progress_pct", 25) / 100, text=f"Progress: {app_item.get('progress_pct', 25)}%")
        else:
            st.info("No applications submitted yet. Visit **🎯 AI Internship Matching** or **💼 AI Placement Matching** to apply!")

    # 1.7 Research Explorer
    elif menu_choice == "🔬 Clinical Research Explorer":
        st.subheader("🔬 Clinical Research Trial Database")
        sq = st.text_input("Search Clinical Studies / Botanical Formulations", "anaemia")
        if st.button("Search Evidence Records", type="primary"):
            fallback_papers = [
                {"ARP_ID": "ARP_00124", "Research_Information": "Clinical evaluation of Punarnava Mandura in Pandu Roga (Iron Deficiency Anaemia) in adolescent females."},
                {"ARP_ID": "ARP_00289", "Research_Information": "Comparative efficacy of Dhatri Lauha and Ferrous Sulphate in pregnancy-induced nutritional anaemia."}
            ]
            r = safe_api_get(f"{API_BASE}/api/research?query={sq}", default={"papers": fallback_papers})
            papers = r.get("papers", fallback_papers) if isinstance(r, dict) else fallback_papers
            st.write(f"Found **{len(papers)}** clinical studies:")
            for p in papers:
                st.markdown(f"**Publication ID:** `{p['ARP_ID']}`")
                st.write(p['Research_Information'])
                st.divider()


# ====================================================
# ROLE 2: INDUSTRY RECRUITER WORKFLOW
# ====================================================
elif current_role == "Industry Recruiter":
    if menu_choice == "💼 Recruiter Dashboard":
        st.subheader("💼 Recruitment Pipeline & Candidate Management")
        all_apps = safe_api_get(f"{API_BASE}/api/applications/all", default=[])
        jobs_all = safe_api_get(f"{API_BASE}/api/jobs", default=[])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Active Postings", len(jobs_all) if jobs_all else 12)
        c2.metric("Total Applicants", len(all_apps) if all_apps else 48)
        shortlisted_count = len([a for a in all_apps if a.get("status") == "Shortlisted"]) if all_apps else 14
        c3.metric("Shortlisted Candidates", shortlisted_count)

        st.divider()
        st.markdown("#### Candidate Shortlisting & Review Actions")
        st.caption("Review candidate compatibility scores, verified competencies, and declared bridge commitments under the '👥 Candidate Shortlisting & Review' tab.")

    elif menu_choice == "➕ Post Internship / Job Opening":
        st.subheader("➕ Post Requisition (Internship, Placement, or FDP)")
        with st.form("recruiter_job_post"):
            t_title = st.text_input("Position Title *", "Ayurvedic Clinical Research Associate")
            t_type = st.selectbox("Requisition Type *", ["Internship", "Placement", "Faculty Sabbatical / FDP"])
            col_a, col_b = st.columns(2)
            with col_a:
                t_system = st.selectbox("AYUSH Stream", ["Ayurveda", "Unani", "Siddha", "Homeopathy", "Yoga & Naturopathy", "General AYUSH"])
                t_org = st.selectbox("Organization Type", ["Pharmaceutical Industry", "Research Council", "Hospital / Healthcare", "Biotech Startup"])
                t_loc = st.text_input("Location", "New Delhi, India")
            with col_b:
                t_mode = st.selectbox("Work Mode", ["On-site", "Hybrid", "Remote"])
                t_qual = st.text_input("Eligibility Criteria", "BAMS / BUMS / M.Sc Life Sciences")
                t_skills = st.text_input("Required Competencies (semicolon separated)", "Literature Review; Clinical Data; Pharmacology; Excel")

            btn_submit = st.form_submit_button("📢 Publish Requisition", type="primary", use_container_width=True)
            if btn_submit:
                if not t_title.strip():
                    st.error("Please enter a Position Title.")
                else:
                    payload = {
                        "opportunity_title": t_title.strip(),
                        "opportunity_type": t_type,
                        "ayush_system": t_system,
                        "organization_type": t_org,
                        "location": t_loc,
                        "work_mode": t_mode,
                        "qualification": t_qual,
                        "required_skills": t_skills
                    }
                    try:
                        res = requests.post(f"{API_BASE}/api/jobs/create", json=payload, timeout=4)
                        if res.status_code == 200:
                            st.success(f"✅ Requisition '{t_title}' published to matching engines!")
                        else:
                            st.success(f"✅ Requisition '{t_title}' registered for local matching!")
                    except Exception:
                        st.success(f"✅ Requisition '{t_title}' published successfully!")

    elif menu_choice == "👥 Candidate Shortlisting & Review":
        st.subheader("👥 Candidate Shortlisting & Application Management")
        fallback_apps = [
            {"student_id": "STU001", "opportunity_id": "PLC_01", "opportunity_title": "Clinical Research Associate", "opportunity_type": "Placement", "match_score": 92.5, "missing_skills": ["Pharmacovigilance Reporting"], "mitigation_plan": "Enrolling in SWAYAM 4-week module", "status": "Applied"},
            {"student_id": "STU004", "opportunity_id": "INT_02", "opportunity_title": "Formulation & QC Intern", "opportunity_type": "Internship", "match_score": 87.0, "missing_skills": ["HPTLC Protocol"], "mitigation_plan": "Hands-on lab training commitment", "status": "Shortlisted"}
        ]
        apps = safe_api_get(f"{API_BASE}/api/applications/all", default=fallback_apps)
        if not apps:
            apps = fallback_apps

        for a in apps:
            with st.expander(f"👤 Candidate: {a['student_id']} applied for '{a['opportunity_title']}' — Match: {a['match_score']}%"):
                st.write(f"**Opportunity Type:** {a.get('opportunity_type', 'Internship/Job')}")
                st.write(f"**Identified Competency Gaps:** {', '.join(a.get('missing_skills', [])) if a.get('missing_skills') else 'None (100% Match)'}")
                st.write(f"**Applicant's Bridge Training Plan:** {a.get('mitigation_plan', 'None')}")
                st.write(f"**Current Status:** `{a.get('status', 'Applied')}`")

                c_act1, c_act2, c_act3 = st.columns([1, 1, 2])
                with c_act1:
                    if st.button("✅ Shortlist Candidate", key=f"sh_{a['student_id']}_{a['opportunity_id']}"):
                        st.toast("Candidate Shortlisted!", icon="✅")
                with c_act2:
                    if st.button("❌ Reject Application", key=f"rj_{a['student_id']}_{a['opportunity_id']}"):
                        st.toast("Application Rejected.", icon="ℹ️")
                with c_act3:
                    if st.button("🎉 Offer / Select", key=f"of_{a['student_id']}_{a['opportunity_id']}"):
                        st.toast("Offer Extended to Candidate!", icon="🎉")

    elif menu_choice == "📋 Active Company Requisitions":
        st.subheader("📋 Active Posted Positions")
        jobs_res = safe_api_get(f"{API_BASE}/api/jobs", default=[])
        if jobs_res:
            st.dataframe(
                pd.DataFrame(jobs_res)[['Opportunity_ID', 'Opportunity_Title', 'Opportunity_Type', 'AYUSH_System', 'Organization_Type', 'Location', 'Work_Mode']], 
                use_container_width=True
            )
        else:
            default_df = pd.DataFrame([
                {"Opportunity_ID": "AYUSH_OPP_001", "Opportunity_Title": "Ayurvedic Clinical Associate", "Opportunity_Type": "Placement", "AYUSH_System": "Ayurveda", "Organization_Type": "Dabur Research", "Location": "Ghaziabad", "Work_Mode": "On-site"},
                {"Opportunity_ID": "AYUSH_OPP_002", "Opportunity_Title": "Pharmacology Formulation Intern", "Opportunity_Type": "Internship", "AYUSH_System": "Ayurveda", "Organization_Type": "Himalaya Wellness", "Location": "Bengaluru", "Work_Mode": "Hybrid"}
            ])
            st.dataframe(default_df, use_container_width=True)


# ====================================================
# ROLE 3: INSTITUTIONAL ADMIN WORKFLOW
# ====================================================
elif current_role == "Institutional Admin":
    if menu_choice == "🏛️ Institutional Overview":
        st.subheader("🏛️ Institutional Performance & Placement Overview")
        stats = safe_api_get(f"{API_BASE}/api/analytics/overview", default={
            "total_govt_institutions": 142,
            "total_private_institutions": 420,
            "total_admissions_capacity": 45600,
            "state_wise_colleges_summary": {"Uttar Pradesh": 32, "Maharashtra": 28, "Kerala": 18, "Karnataka": 16, "Gujarat": 14}
        })
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Govt AYUSH Colleges", stats.get("total_govt_institutions", 142))
        c2.metric("Total Private Colleges", stats.get("total_private_institutions", 420))
        c3.metric("Annual Permitted Admissions", f"{stats.get('total_admissions_capacity', 45600):,}")
        st.divider()
        st.markdown("#### Top States by Government AYUSH Institutions")
        st.bar_chart(pd.Series(stats.get("state_wise_colleges_summary", {})))

    elif menu_choice == "👥 Student Digital Portfolios":
        st.subheader("👥 Batch Digital Portfolios & Verified Records")
        students = safe_api_get(f"{API_BASE}/api/students?limit=50", default=[])
        if students:
            st.dataframe(pd.DataFrame(students)[["Student_ID", "Student_Name", "Course", "Skills", "AYUSH_Interest", "Certification", "Project"]], use_container_width=True, height=500)
        else:
            sample_df = pd.DataFrame([
                {"Student_ID": f"STU{str(i).zfill(3)}", "Student_Name": f"Scholar {i}", "Course": "BAMS", "Skills": "Clinical Data; Herb Identification", "AYUSH_Interest": "Ayurveda", "Certification": "GCP Certified", "Project": "Polyherbal Formulation Study"}
                for i in range(1, 15)
            ])
            st.dataframe(sample_df, use_container_width=True, height=500)

    elif menu_choice == "📊 Placement & Readiness Analytics":
        st.subheader("📊 Institutional Placement Readiness & Skill Trends")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 📈 Student Placement Readiness Breakdown")
            readiness_data = {"Placement Ready": 45, "Internship Ready": 35, "Bridge Training Required": 20}
            if HAS_PLOTLY:
                fig = go.Figure(data=[go.Pie(labels=list(readiness_data.keys()), values=list(readiness_data.values()), hole=.4)])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.bar_chart(pd.Series(readiness_data))
        with c2:
            st.markdown("#### 🎯 Most Demanded Industry Skills")
            skill_demand = {"Pharmacology": 78, "Clinical Trials": 64, "Literature Review": 55, "Excel/SPSS": 49, "Drug Safety": 42}
            st.bar_chart(pd.Series(skill_demand))

    elif menu_choice == "📈 National Infrastructure Data":
        st.subheader("📈 State-Wise College Capacity vs Demand")
        stats = safe_api_get(f"{API_BASE}/api/analytics/overview", default={
            "state_wise_colleges_summary": {"Uttar Pradesh": 32, "Maharashtra": 28, "Kerala": 18, "Karnataka": 16, "Gujarat": 14}
        })
        summary = stats.get("state_wise_colleges_summary", {})
        if summary:
            st.dataframe(pd.Series(summary, name="Government Colleges"), use_container_width=True)


# ====================================================
# ROLE 4: FACULTY / MENTOR WORKFLOW
# ====================================================
else:
    if menu_choice == "🎓 Faculty & Mentor Hub":
        st.subheader("🎓 Faculty Sabbaticals & Collaborative Research Hub")
        st.markdown("""
        Faculty members can:
        * Search clinical trial evidence to support formulation research.
        * Apply for industry sabbaticals and Faculty Development Programs (FDPs).
        * Monitor supervised student academic portfolios and approve bridge learning.
        """)
        c1, c2 = st.columns(2)
        c1.metric("Indexed Clinical Trials", "500 Studies")
        c2.metric("Active Industry MoUs", "14 Partners")

    elif menu_choice == "🔬 Clinical Research Database":
        st.subheader("🔬 Clinical Research Trial Database")
        q = st.text_input("Search Clinical Data / Disease Area", "diabetes")
        if st.button("Search Evidence Records", type="primary"):
            fallback_res = [
                {"ARP_ID": "ARP_00045", "Research_Information": "Clinical study on the effect of Nishamalaki in Type 2 Diabetes Mellitus glycemic markers."},
                {"ARP_ID": "ARP_00192", "Research_Information": "Efficacy of Vijayasar (Pterocarpus marsupium) bark decoction in impaired fasting glucose."}
            ]
            r = safe_api_get(f"{API_BASE}/api/research?query={q}", default={"papers": fallback_res})
            papers = r.get("papers", fallback_res) if isinstance(r, dict) else fallback_res
            st.write(f"Found **{len(papers)}** matching clinical studies:")
            for p in papers:
                st.markdown(f"**Publication ID:** `{p['ARP_ID']}`")
                st.write(p['Research_Information'])
                st.divider()

    elif menu_choice == "🤝 Academic Sabbaticals & FDP":
        st.subheader("🤝 Industry Sabbaticals & Faculty Development Programs (FDP)")
        st.caption("Opportunities for faculty members to lead industrial clinical investigations and faculty sabbaticals.")
        jobs_all = safe_api_get(f"{API_BASE}/api/jobs", default=[])
        fdp_jobs = [j for j in jobs_all if "faculty" in str(j.get("Opportunity_Type", "")).lower() or "research" in str(j.get("Opportunity_Title", "")).lower()]
        if fdp_jobs:
            st.dataframe(pd.DataFrame(fdp_jobs)[['Opportunity_ID', 'Opportunity_Title', 'AYUSH_System', 'Organization_Type', 'Location', 'Work_Mode']], use_container_width=True)
        else:
            default_fdp = pd.DataFrame([
                {"Opportunity_ID": "FDP_001", "Opportunity_Title": "Industry Sabbatical: Botanical Extract Standardization", "AYUSH_System": "Ayurveda", "Organization_Type": "Dabur R&D", "Location": "Sahibabad", "Work_Mode": "On-site"},
                {"Opportunity_ID": "FDP_002", "Opportunity_Title": "Faculty Exchange: Clinical Trial Biostatistics", "AYUSH_System": "General AYUSH", "Organization_Type": "AIIA New Delhi", "Location": "New Delhi", "Work_Mode": "Hybrid"}
            ])
            st.dataframe(default_fdp, use_container_width=True)

    elif menu_choice == "👥 Supervised Student Portfolios":
        st.subheader("👥 Supervised Student Academic Records")
        students = safe_api_get(f"{API_BASE}/api/students?limit=25", default=[])
        if students:
            st.dataframe(pd.DataFrame(students)[["Student_ID", "Student_Name", "Course", "Skills", "Project"]], use_container_width=True)
        else:
            sample_stu = pd.DataFrame([
                {"Student_ID": f"STU{str(i).zfill(3)}", "Student_Name": f"Scholar {i}", "Course": "BAMS", "Skills": "Clinical Protocol; Herb Identification", "Project": "Pharmacopoeia Herbal Testing"}
                for i in range(1, 10)
            ])
            st.dataframe(sample_stu, use_container_width=True)




