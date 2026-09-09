import json
from typing import Dict, Any, List, Optional
from app.services.gemini_service import gemini_service
from app.services.activity_service import activity_service

class SemanticMatcher:
    async def evaluate_match(self, candidate_profile: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates candidate fit against a job listing using Gemini API.
        Returns match score (0-100), rationale, matching skills, and gap analysis.
        """
        company = job_data.get("company_name", "Company")
        role_title = job_data.get("role_title", "Role")
        job_desc = job_data.get("job_description", "")[:2500] # Cap description for optimal latency
        
        skills = candidate_profile.get("skills", {})
        projects = candidate_profile.get("projects", [])
        experience = candidate_profile.get("experience", [])
        education = candidate_profile.get("education", [])

        candidate_summary = {
            "name": candidate_profile.get("full_name"),
            "skills": skills,
            "education": [f"{e.get('degree')} from {e.get('institution')} (Grad: {e.get('graduation_date')})" for e in education],
            "experience": [f"{exp.get('title')} at {exp.get('company')}: {', '.join(exp.get('highlights', [])[:2])}" for exp in experience],
            "projects": [f"{p.get('name')} ({', '.join(p.get('tech_stack', []))}): {p.get('description')}" for p in projects]
        }

        system_instruction = (
            "You are a principal technical hiring director evaluating an internship candidate. "
            "Compare the candidate's verified profile against the job description. "
            "Score the match from 0 to 100 based on technical alignment, relevant project experience, and prerequisite skills. "
            "Be objective, constructive, and accurate. Return ONLY JSON."
        )

        prompt = f"""
Candidate Profile:
{json.dumps(candidate_summary, indent=2)}

Job Details:
- Company: {company}
- Role: {role_title}
- Location: {job_data.get('location')}
- Description & Requirements:
{job_desc}

Evaluate the candidate's fit and return JSON matching this exact structure:
{{
  "match_score": 88,
  "match_rationale": "2-3 concise sentences explaining why the candidate matches this role and any specific strengths.",
  "matching_skills": ["Python", "FastAPI", "Distributed Systems"],
  "gap_skills": ["C++", "AWS CDK"],
  "is_internship_confirmed": true,
  "recommendation": "STRONG_MATCH"
}}
"""

        try:
            if gemini_service.is_available():
                result = await gemini_service.generate_json(prompt, system_instruction)
                if result and "match_score" in result:
                    return {
                        "match_score": int(result.get("match_score", 70)),
                        "match_rationale": result.get("match_rationale", "Good alignment with candidate skillset."),
                        "matching_skills": result.get("matching_skills", []),
                        "gap_skills": result.get("gap_skills", []),
                        "recommendation": result.get("recommendation", "MODERATE_MATCH")
                    }
        except Exception as e:
            print(f"[SemanticMatcher] Gemini matching error: {e}")

        # Deterministic heuristic fallback
        return self._heuristic_match(candidate_profile, job_data)

    def _heuristic_match(self, candidate_profile: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates keyword and title overlap as a robust offline fallback."""
        title = job_data.get("role_title", "").lower()
        desc = job_data.get("job_description", "").lower()
        
        all_skills = []
        skills_dict = candidate_profile.get("skills", {})
        if isinstance(skills_dict, dict):
            for k, skill_list in skills_dict.items():
                if isinstance(skill_list, list):
                    all_skills.extend([s.lower() for s in skill_list])
        
        # Calculate overlap
        matched_skills = []
        for skill in set(all_skills):
            if skill in desc or skill in title:
                matched_skills.append(skill.capitalize())

        base_score = 65
        if any(term in title for term in ["software", "swe", "engineer", "developer", "backend", "full stack", "frontend", "intern"]):
            base_score += 15
        
        score = min(96, base_score + len(matched_skills) * 3)

        rationale = (
            f"Candidate matches {len(matched_skills)} core technical skills ({', '.join(matched_skills[:4])}) "
            f"relevant to the {job_data.get('role_title')} position at {job_data.get('company_name')}."
        )

        return {
            "match_score": score,
            "match_rationale": rationale,
            "matching_skills": matched_skills[:6],
            "gap_skills": [],
            "recommendation": "STRONG_MATCH" if score >= 80 else "MODERATE_MATCH"
        }

semantic_matcher = SemanticMatcher()
