from groq import Groq
import json
import os
import re

# ---------------- INIT CLIENT ----------------
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing in environment variables")

client = Groq(api_key=api_key)


# ---------------- CORE FUNCTION ----------------
def analyze_resume(resume_text, user_goal):

    prompt = f"""
You are an expert software engineer and hiring manager.

Analyze this resume based on the user's goal.

User Goal: {user_goal}

STRICT INSTRUCTIONS:
- Extract ONLY relevant skills
- Remove irrelevant tools
- Identify skill gaps clearly
- Suggest learning roadmap for missing skills
- Generate interview questions based on goal
- Output MUST be valid JSON only

Return format:
{{
  "skills": [],
  "missing_skills": [],
  "roadmap": [],
  "interview_questions": []
}}

Resume:
{resume_text}
"""

    try:
        # ---------------- GROQ API CALL ----------------
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        # ---------------- SAFE JSON EXTRACTION ----------------
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if not match:
            return {
                "error": "No valid JSON found",
                "raw_output": content
            }

        result = json.loads(match.group())

        # ---------------- ATS SCORE CALCULATION ----------------
        text = resume_text.lower()

        skills = result.get("skills", [])
        missing = result.get("missing_skills", [])

        matched = len(skills)
        total = matched + len(missing)

        # Skills Score (50)
        skills_score = int((matched / total) * 50) if total > 0 else 20

        # Projects Score (20)
        project_keywords = ["project", "built", "developed", "created"]
        projects_score = 20 if any(k in text for k in project_keywords) else 8

        # Education Score (15)
        edu_keywords = ["b.tech", "bachelor", "degree", "engineering"]
        education_score = 15 if any(k in text for k in edu_keywords) else 7

        # Resume Quality Score (15)
        quality_score = 15 if len(resume_text) > 300 else 8

        ats_score = min(100, skills_score + projects_score + education_score + quality_score)

        result["ats_score"] = ats_score

        return result

    except json.JSONDecodeError:
        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "ats_score": 0,
            "error": "Invalid JSON returned by model"
        }

    except Exception as e:
        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "ats_score": 0,
            "error": str(e)
        }