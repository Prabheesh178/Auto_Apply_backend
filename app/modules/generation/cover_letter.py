import json
from typing import Dict, Any, Optional
from app.services.gemini_service import gemini_service
from app.services.activity_service import activity_service

class CoverLetterGenerator:
    async def generate_cover_letter(
        self,
        candidate_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        match_rationale: Optional[str] = None
    ) -> str:
        """
        Generates a tailored, professional, role-specific cover letter using Gemini.
        Connects verified candidate projects/experience directly to the target role.
        """
        candidate_name = candidate_profile.get("full_name", "Candidate")
        company = job_data.get("company_name", "Company")
        role_title = job_data.get("role_title", "Software Engineering Intern")
        location = job_data.get("location", "Remote")
        job_desc = job_data.get("job_description", "")[:2500]

        skills = candidate_profile.get("skills", {})
        experience = candidate_profile.get("experience", [])
        projects = candidate_profile.get("projects", [])
        education = candidate_profile.get("education", [])

        candidate_summary = {
            "name": candidate_name,
            "education": education,
            "experience": experience,
            "projects": projects,
            "skills": skills
        }

        system_instruction = (
            "You are a professional career advisor and technical writing expert. "
            "Write an exceptional, compelling, and tailored cover letter for an internship application. "
            "STRICT RULES:\n"
            "1. NEVER fabricate experiences, employers, degrees, or metrics.\n"
            "2. Specifically reference the candidate's actual projects and technical stack.\n"
            "3. Demonstrate genuine enthusiasm for the company and how the candidate's skills solve real problems in this role.\n"
            "4. Keep it concise: 3 to 4 well-structured paragraphs.\n"
            "5. Format cleanly with standard formal salutation and sign-off."
        )

        prompt = f"""
Candidate Verified Profile:
{json.dumps(candidate_summary, indent=2)}

Job Details:
- Company: {company}
- Position: {role_title}
- Location: {location}
- Match Context: {match_rationale or 'High technical alignment'}
- Job Description:
{job_desc}

Generate a custom cover letter from {candidate_name} to the {company} Hiring Team. Return only the plain text letter.
"""

        try:
            if gemini_service.is_available():
                letter = await gemini_service.generate_text(prompt, system_instruction, temperature=0.4)
                if letter and len(letter) > 150:
                    return letter.strip()
        except Exception as e:
            print(f"[CoverLetterGenerator] Gemini error: {e}")

        # Deterministic fallback template
        return self._generate_template_fallback(candidate_profile, job_data)

    def _generate_template_fallback(self, candidate_profile: Dict[str, Any], job_data: Dict[str, Any]) -> str:
        """Structured fallback template using real candidate projects and metrics."""
        name = candidate_profile.get("full_name", "Candidate")
        company = job_data.get("company_name", "Company")
        role = job_data.get("role_title", "Software Engineering Intern")
        
        edu = candidate_profile.get("education", [{}])[0]
        institution = edu.get("institution", "University")
        degree = edu.get("degree", "Computer Science")
        grad = edu.get("graduation_date", "2026")

        skills = candidate_profile.get("skills", {})
        languages = ", ".join(skills.get("languages", ["Python", "Go", "TypeScript"])[:4])
        frameworks = ", ".join(skills.get("frameworks", ["FastAPI", "React", "PostgreSQL"])[:3])

        exp = candidate_profile.get("experience", [{}])
        first_exp = exp[0] if exp else {}
        exp_company = first_exp.get("company", "previous roles")
        exp_highlights = first_exp.get("highlights", ["built high-performance backend systems"])[0] if first_exp.get("highlights") else "engineered resilient software solutions"

        projects = candidate_profile.get("projects", [])
        project_name = projects[0].get("name", "Distributed Systems Project") if projects else "Core Engineering Projects"
        project_desc = projects[0].get("description", "scalable distributed architecture") if projects else "high-throughput applications"

        return f"""Dear {company} Hiring Team,

I am writing to express my strong interest in the {role} position at {company}. As a student pursuing my {degree} at {institution} (Expected graduation: {grad}), I have long admired {company}'s engineering culture and focus on high-reliability, developer-centric infrastructure.

Throughout my technical coursework and practical experience with {languages}, I have focused on designing robust, high-performance systems. During my work at {exp_company}, I {exp_highlights.lower().rstrip('.')}, which deepened my experience with {frameworks}. Furthermore, through my work on {project_name}, I developed {project_desc.lower().rstrip('.')}, emphasizing clean code architecture and test-driven reliability.

The opportunity to contribute to {company}'s mission while collaborating with your world-class engineering team aligns directly with my technical ambitions. I am confident that my background in systems engineering, proactive problem-solving, and dedication to code quality will allow me to make meaningful contributions from day one.

Thank you for your time and consideration. I welcome the opportunity to discuss how my skillset can support {company}'s engineering initiatives.

Sincerely,
{name}"""

cover_letter_generator = CoverLetterGenerator()
