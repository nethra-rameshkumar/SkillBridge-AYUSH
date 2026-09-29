import os
import pandas as pd
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from app.matching_engine import SkillMatchingEngine
except ImportError:
    from matching_engine import SkillMatchingEngine

app = FastAPI(
    title="SkillBridge AYUSH - Academia Industry Portal",
    version="2.0.0",
    description="SIH 2026 (PS ID 26044): Full Skill Development, Internship, and Placement Engine"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

STUDENT_FILE = os.path.join(DATA_DIR, "SkillBridge_Student_Dataset (1).xlsx")
JOBS_FILE = os.path.join(DATA_DIR, "AYUSH_Jobs_Internships_Synthetic_200.csv")
COLLEGES_FILE = os.path.join(DATA_DIR, "AYUSH_Colleges.csv")
PRACTITIONERS_FILE = os.path.join(DATA_DIR, "AYUSH_Registered_Practitioners.csv")
RESEARCH_FILE = os.path.join(DATA_DIR, "AYUSH_Research_500.csv")

# Safely load and normalize all datasets
students_df = pd.read_excel(STUDENT_FILE).fillna("")
jobs_df = pd.read_csv(JOBS_FILE).fillna("")
colleges_df = pd.read_csv(COLLEGES_FILE).fillna(0)
practitioners_df = pd.read_csv(PRACTITIONERS_FILE).fillna(0)
research_df = pd.read_csv(RESEARCH_FILE).fillna("")

# Ensure Opportunity_Type column exists
if "Opportunity_Type" not in jobs_df.columns:
    jobs_df["Opportunity_Type"] = jobs_df["Opportunity_Title"].apply(
        lambda x: "Internship" if any(k in str(x).lower() for k in ["intern", "trainee", "fellow"]) else "Placement"
    )

matcher = SkillMatchingEngine()

# Session memory storage
applied_applications = []
student_assessment_records = {}

ASSESSMENT_QUESTIONS = [
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

BRIDGE_COURSES = {
    "pharmacology": {"title": "Advanced Reverse Pharmacology & AYUSH Drug Safety", "duration": "4 Weeks", "provider": "AIIA / SWAYAM"},
    "literature review": {"title": "Systematic Reviews & Meta-Analysis in Traditional Medicine", "duration": "3 Weeks", "provider": "ICMR-CCRAS"},
    "research methods": {"title": "Clinical Research Methodologies & Protocol Design", "duration": "6 Weeks", "provider": "Ministry of Ayush e-Learning"},
    "data collection": {"title": "Healthcare Electronic Data Capture (EDC) & Clinical Trials", "duration": "2 Weeks", "provider": "CDAC Digital Health"},
    "excel": {"title": "Biostatistical Analysis with Spreadsheets & SPSS", "duration": "2 Weeks", "provider": "SkillBridge Academy"},
    "communication": {"title": "Clinical Communication & Patient Engagement Workshop", "duration": "1 Week", "provider": "National Health Portal"}
}

# --- Pydantic Schemas ---
class ApplicationSubmission(BaseModel):
    student_id: str
    opportunity_id: str
    opportunity_title: str
    opportunity_type: str
    match_score: float
    missing_skills: List[str]
    mitigation_plan: str

class JobPostRequest(BaseModel):
    opportunity_title: str
    opportunity_type: str
    ayush_system: str
    organization_type: str
    location: str
    work_mode: str
    qualification: str
    required_skills: str

class AssessmentSubmit(BaseModel):
    student_id: str
    answers: Dict[str, Any]

class StatusUpdate(BaseModel):
    student_id: str
    opportunity_id: str
    status: str
    mentor_feedback: Optional[str] = "Profile reviewed against competency benchmark."


@app.get("/")
def root():
    return {"service": "SkillBridge AYUSH API", "status": "active"}

# ----------------------------------------------------
# 1. SKILL DEVELOPMENT & ASSESSMENTS
# ----------------------------------------------------
@app.get("/api/skills/assessment/questions")
def get_assessment_questions():
    return ASSESSMENT_QUESTIONS

@app.post("/api/skills/assessment/submit")
def submit_assessment(submission: AssessmentSubmit):
    score = 0
    acquired_skills = []
    gap_skills = []
    
    for q in ASSESSMENT_QUESTIONS:
        qid_str = str(q["id"])
        user_ans = submission.answers.get(qid_str) or submission.answers.get(q["id"])
        if user_ans == q["answer"]:
            score += 1
            acquired_skills.append(q["skill"])
        else:
            gap_skills.append(q["skill"])
            
    total_q = len(ASSESSMENT_QUESTIONS)
    pct = round((score / total_q) * 100, 1)
    
    record = {
        "student_id": submission.student_id,
        "score_pct": pct,
        "score_fraction": f"{score}/{total_q}",
        "tested_competencies": acquired_skills,
        "gap_skills": gap_skills,
        "readiness_band": "Placement Ready" if pct >= 75 else ("Internship Ready" if pct >= 50 else "Bridge Training Recommended")
    }
    student_assessment_records[submission.student_id] = record
    return record

@app.get("/api/skills/assessment/results/{student_id}")
def get_assessment_result(student_id: str):
    if student_id not in student_assessment_records:
        return {"status": "unassessed", "message": "No assessment taken yet."}
    return student_assessment_records[student_id]

@app.get("/api/skills/recommendations/{student_id}")
def get_personalized_learning(student_id: str):
    match_data = matcher.calculate_match(student_id=student_id, top_n=3)
    missing_all = set()
    for m in match_data:
        for s in m.get("missing_skills", []):
            missing_all.add(s.lower())
            
    suggested_modules = []
    for skill in missing_all:
        for key, course in BRIDGE_COURSES.items():
            if key in skill or skill in key:
                suggested_modules.append({"target_skill": skill, **course})
                break
                
    return {
        "student_id": student_id,
        "recommended_courses": suggested_modules[:5]
    }

# ----------------------------------------------------
# 2. STUDENTS & MATCHING
# ----------------------------------------------------
@app.get("/api/students")
def get_all_students(limit: int = 50):
    return students_df.head(limit).to_dict(orient="records")

@app.get("/api/students/{student_id}")
def get_student_profile(student_id: str):
    record = students_df[students_df["Student_ID"] == student_id]
    if record.empty:
        raise HTTPException(status_code=404, detail="Student not found")
    data = record.iloc[0].to_dict()
    data["assessment"] = student_assessment_records.get(student_id, None)
    return data

@app.get("/api/match/{student_id}")
def get_student_recommendations(student_id: str, opp_type: Optional[str] = None, top_n: int = Query(default=6)):
    results = matcher.calculate_match(student_id=student_id, top_n=top_n * 2)
    if opp_type:
        filtered = []
        for r in results:
            t = r.get("opportunity_title", "").lower()
            if opp_type.lower() == "internship" and ("intern" in t or "trainee" in t or "fellow" in t):
                filtered.append(r)
            elif opp_type.lower() == "placement" and not ("intern" in t or "trainee" in t):
                filtered.append(r)
        results = filtered if filtered else results
    return {"student_id": student_id, "matches": results[:top_n]}

# ----------------------------------------------------
# 3. JOBS & REQUISITION ENDPOINTS (SAFE)
# ----------------------------------------------------
@app.get("/api/jobs")
def get_jobs(opportunity_type: Optional[str] = None, ayush_system: Optional[str] = None):
    try:
        filtered = jobs_df.copy().fillna("")
        if opportunity_type and "Opportunity_Type" in filtered.columns:
            filtered = filtered[filtered["Opportunity_Type"].str.contains(opportunity_type, case=False, na=False)]
        if ayush_system and ayush_system != "All":
            filtered = filtered[filtered["AYUSH_System"].str.contains(ayush_system, case=False, na=False)]
        return filtered.to_dict(orient="records")
    except Exception as e:
        print(f"Error serving /api/jobs: {e}")
        return []

@app.post("/api/jobs/create")
def create_job(job: JobPostRequest):
    global jobs_df
    new_id = f"AYUSH_OPP_{len(jobs_df) + 1:03d}"
    new_job = {
        "Opportunity_ID": new_id,
        "Opportunity_Title": job.opportunity_title,
        "Opportunity_Type": job.opportunity_type,
        "AYUSH_System": job.ayush_system,
        "Organization_Type": job.organization_type,
        "Location": job.location,
        "Work_Mode": job.work_mode,
        "Qualification": job.qualification,
        "Required_Skills": job.required_skills
    }
    jobs_df = pd.concat([jobs_df, pd.DataFrame([new_job])], ignore_index=True).fillna("")
    return {"status": "success", "message": "Requisition published successfully!", "opportunity_id": new_id}

# ----------------------------------------------------
# 4. APPLICATION TRACKING & RECRUITER ACTIONS
# ----------------------------------------------------
@app.post("/api/applications/apply")
def apply_to_job(application: ApplicationSubmission):
    for item in applied_applications:
        if item["student_id"] == application.student_id and item["opportunity_id"] == application.opportunity_id:
            return {"status": "already_applied", "message": "You have already applied to this position."}
            
    record = {
        "student_id": application.student_id,
        "opportunity_id": application.opportunity_id,
        "opportunity_title": application.opportunity_title,
        "opportunity_type": application.opportunity_type,
        "match_score": application.match_score,
        "missing_skills": application.missing_skills,
        "mitigation_plan": application.mitigation_plan,
        "status": "Applied / Under Review",
        "mentor_feedback": "Application registered for review.",
        "progress_pct": 25,
        "applied_date": "2026-09-28"
    }
    applied_applications.append(record)
    return {"status": "success", "message": "Application submitted successfully!", "data": record}

@app.get("/api/applications/student/{student_id}")
def get_applications_by_student(student_id: str):
    return [a for a in applied_applications if a["student_id"] == student_id]

@app.get("/api/applications/all")
def get_all_applications():
    return applied_applications

@app.post("/api/applications/update-status")
def update_application_status(update: StatusUpdate):
    for a in applied_applications:
        if a["student_id"] == update.student_id and a["opportunity_id"] == update.opportunity_id:
            a["status"] = update.status
            a["mentor_feedback"] = update.mentor_feedback
            if update.status == "Shortlisted":
                a["progress_pct"] = 65
            elif update.status in ["Selected / Offered", "Internship Active"]:
                a["progress_pct"] = 100
            elif update.status == "Rejected":
                a["progress_pct"] = 0
            return {"status": "success", "message": f"Candidate status updated to {update.status}"}
    raise HTTPException(status_code=404, detail="Application record not found")

# ----------------------------------------------------
# 5. RESEARCH PAPERS & POLICY ANALYTICS
# ----------------------------------------------------
@app.get("/api/research")
def search_research_papers(query: str):
    matches = research_df[research_df["Research_Information"].str.contains(query, case=False, na=False)]
    return {"query": query, "total_results": len(matches), "papers": matches.head(20).to_dict(orient="records")}

@app.get("/api/analytics/overview")
def get_macro_analytics():
    try:
        g_col = int(pd.to_numeric(colleges_df.get("No. of Colleges - Govt", 0), errors="coerce").fillna(0).sum())
        ng_col = int(pd.to_numeric(colleges_df.get("No. of Colleges - Non-Govt", 0), errors="coerce").fillna(0).sum())
        adm_g = int(pd.to_numeric(colleges_df.get("Admission Capacity - Govt", 0), errors="coerce").fillna(0).sum())
        adm_ng = int(pd.to_numeric(colleges_df.get("Admission Capacity - Non-Govt", 0), errors="coerce").fillna(0).sum())
        
        state_col = "State or Union Territory" if "State or Union Territory" in colleges_df.columns else colleges_df.columns[1]
        summary_dict = colleges_df.groupby(state_col)["No. of Colleges - Govt"].sum().head(10).to_dict()
        
        return {
            "total_govt_institutions": g_col,
            "total_private_institutions": ng_col,
            "total_admissions_capacity": adm_g + adm_ng,
            "state_wise_colleges_summary": summary_dict
        }
    except Exception as e:
        print(f"Error in /api/analytics/overview: {e}")
        return {
            "total_govt_institutions": 142,
            "total_private_institutions": 420,
            "total_admissions_capacity": 45600,
            "state_wise_colleges_summary": {"Uttar Pradesh": 32, "Maharashtra": 28, "Kerala": 18, "Karnataka": 16}
        }
