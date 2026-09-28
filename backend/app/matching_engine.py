import os
import pandas as pd
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Handle both app/ and app/routes/ execution locations
if os.path.basename(BASE_DIR) == "backend":
    DATA_DIR = os.path.join(BASE_DIR, "data")
else:
    DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")

STUDENT_FILE = os.path.join(DATA_DIR, "SkillBridge_Student_Dataset (1).xlsx")
JOBS_FILE = os.path.join(DATA_DIR, "AYUSH_Jobs_Internships_Synthetic_200.csv")


class SkillMatchingEngine:
    def __init__(self):
        self.students_df = pd.read_excel(STUDENT_FILE)
        self.jobs_df = pd.read_csv(JOBS_FILE)

    def _parse_skills(self, text: str) -> List[str]:
        if pd.isna(text):
            return []
        delimiter = ';' if ';' in str(text) else ','
        return [s.strip().lower() for s in str(text).split(delimiter) if s.strip()]

    def calculate_match(self, student_id: str, top_n: int = 5) -> List[Dict[str, Any]]:
        student_row = self.students_df[self.students_df['Student_ID'] == student_id]
        if student_row.empty:
            return []

        student = student_row.iloc[0]
        s_course = str(student['Course']).lower()
        s_interest = str(student['AYUSH_Interest']).lower()
        s_cert = str(student['Certification']).lower()
        s_proj = str(student['Project']).lower()
        s_skills = self._parse_skills(student['Skills'])
        
        # Comprehensive profile text
        full_student_profile = f"{s_course} {s_interest} {s_cert} {s_proj} {' '.join(s_skills)}"

        results = []
        for _, job in self.jobs_df.iterrows():
            job_sys = str(job['AYUSH_System']).lower()
            job_qual = str(job['Qualification']).lower()
            job_skills = self._parse_skills(job['Required_Skills'])

            # 1. AYUSH System Alignment (Weight: 35%)
            sys_score = 0.0
            if job_sys in s_course or job_sys in s_interest or job_sys in full_student_profile:
                sys_score = 35.0
            elif 'general' in job_sys or 'ayush' in job_sys:
                sys_score = 20.0

            # 2. Skill Overlap & Sub-token Match (Weight: 45%)
            matched_skills = []
            missing_skills = []

            for r_skill in job_skills:
                # Direct match or partial sub-phrase match
                hit = False
                for s_skill in s_skills:
                    if r_skill in s_skill or s_skill in r_skill or any(w in s_skill for w in r_skill.split() if len(w) > 3):
                        hit = True
                        break
                if not hit and (r_skill in full_student_profile):
                    hit = True

                if hit:
                    matched_skills.append(r_skill)
                else:
                    missing_skills.append(r_skill)

            skill_ratio = len(matched_skills) / max(len(job_skills), 1)
            skill_score = skill_ratio * 45.0

            # 3. Qualification Match (Weight: 20%)
            qual_score = 10.0
            for degree in ['bams', 'bums', 'bhms', 'bsms', 'm.d.', 'm.sc', 'nursing']:
                if degree in s_course and degree in job_qual:
                    qual_score = 20.0
                    break

            final_score = round(sys_score + skill_score + qual_score, 1)

            results.append({
                "opportunity_id": job['Opportunity_ID'],
                "opportunity_title": job['Opportunity_Title'],
                "ayush_system": job['AYUSH_System'],
                "organization_type": job['Organization_Type'],
                "location": job['Location'],
                "work_mode": job['Work_Mode'],
                "match_score": min(final_score, 100.0),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "qualification": job['Qualification'],
            })

        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:top_n]


if __name__ == "__main__":
    engine = SkillMatchingEngine()
    test_id = "STU001"
    recs = engine.calculate_match(test_id, top_n=3)
    print(f"\n--- Domain-Aware Job Recommendations for {test_id} ---")
    for r in recs:
        print(f"\nRole: {r['opportunity_title']} ({r['ayush_system']})")
        print(f"Match Score: {r['match_score']}%")
        print(f"Matched Skills: {r['matched_skills']}")
        print(f"Missing Skill Gap: {r['missing_skills']}")
        