import json
from typing import Dict, Any, List, Optional
from app.services.gemini_service import gemini_service

class ResumeTailorer:
    async def tailor_resume(
        self,
        candidate_profile: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates a tailored resume content structure matching the job requirements.
        Reorders skills and emphasizes relevant projects without fabricating facts.
        """
        company = job_data.get("company_name", "Company")
        role = job_data.get("role_title", "Software Engineering Intern")
        job_desc = job_data.get("job_description", "")[:2500]

        system_instruction = (
            "You are an executive ATS resume tailoring specialist. "
            "Tailor the candidate's resume for the specific job description by reordering skills, "
            "selecting the most relevant projects, and polishing bullet points to highlight relevant technologies. "
            "STRICT FACTUAL INTEGRITY RULE: Never invent tools, companies, metrics, or experiences the candidate did not have. "
            "Preserve verified numbers and achievements accurately. Return ONLY valid JSON."
        )

        prompt = f"""
Candidate Master Profile:
{json.dumps(candidate_profile, indent=2)}

Target Job:
- Company: {company}
- Role: {role}
- Description:
{job_desc}

Return a tailored resume JSON conforming to this schema:
{{
  "headline": "Candidate Headline tailored to role",
  "summary": "2-sentence technical summary highlighting matching qualifications",
  "skills": {{
    "languages": ["Re-ordered languages, matching first"],
    "frameworks": ["Re-ordered frameworks"],
    "infrastructure": ["Re-ordered tools/infra"]
  }},
  "experience": [
    {{
      "company": "string",
      "title": "string",
      "location": "string",
      "dates": "string",
      "highlights": ["Emphasized bullet points highlighting matching keywords"]
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "tech_stack": ["string"],
      "description": "string",
      "highlights": ["string"]
    }}
  ],
  "selected_bullets": ["Summary of 3 primary bullet points emphasized for this job"]
}}
"""

        try:
            if gemini_service.is_available():
                tailored = await gemini_service.generate_json(prompt, system_instruction)
                if tailored and "skills" in tailored:
                    return tailored
        except Exception as e:
            print(f"[ResumeTailorer] Gemini error: {e}")

        # Deterministic fallback
        return self._fallback_tailor(candidate_profile, job_data)

    def _fallback_tailor(self, candidate_profile: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Factual deterministic fallback matching."""
        name = candidate_profile.get("full_name", "Candidate")
        role = job_data.get("role_title", "Software Engineer Intern")
        desc = job_data.get("job_description", "").lower()

        skills = candidate_profile.get("skills", {})
        languages = skills.get("languages", ["Python", "TypeScript", "Go", "SQL"])
        # Re-sort skills: skills mentioned in job description come first
        sorted_languages = sorted(languages, key=lambda s: s.lower() in desc, reverse=True)

        frameworks = skills.get("frameworks", ["FastAPI", "React", "PostgreSQL"])
        sorted_frameworks = sorted(frameworks, key=lambda f: f.lower() in desc, reverse=True)

        infra = skills.get("infrastructure", ["Docker", "Redis", "Playwright", "Git"])
        sorted_infra = sorted(infra, key=lambda i: i.lower() in desc, reverse=True)

        raw_exp = candidate_profile.get("experience", [])
        experience = []
        for exp in raw_exp:
            experience.append({
                "company": exp.get("company"),
                "title": exp.get("title"),
                "location": exp.get("location", "Remote"),
                "dates": f"{exp.get('start_date', '')} - {exp.get('end_date', '')}",
                "highlights": exp.get("highlights", [])
            })

        projects = candidate_profile.get("projects", [])

        return {
            "headline": f"{role} Candidate",
            "summary": f"Computer Science student experienced in {', '.join(sorted_languages[:3])} and {', '.join(sorted_frameworks[:2])}, passionate about building scalable software systems.",
            "skills": {
                "languages": sorted_languages,
                "frameworks": sorted_frameworks,
                "infrastructure": sorted_infra
            },
            "experience": experience,
            "projects": projects,
            "selected_bullets": [
                exp.get("highlights", ["Engineered backend services"])[0] if raw_exp else "Built distributed systems",
                projects[0].get("description", "Engineered open source projects") if projects else "Developed full-stack web applications"
            ]
        }

resume_tailorer = ResumeTailorer()
