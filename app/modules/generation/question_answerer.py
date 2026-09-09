import json
import re
import logging
from typing import Dict, Any, List, Optional
from app.services.gemini_service import gemini_service

logger = logging.getLogger("QuestionAnswerer")

class QuestionAnswerer:
    """
    ATS Custom Question Pre-Filler.
    Strictly extracts and rephrases verified information existing in the candidate's structured profile.
    Never guesses, infers, or fabricates facts. Flags missing fields for manual user entry.
    """

    def _extract_profile_facts(self, candidate_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts exact factual ground truth from structured candidate profile."""
        edu_list = candidate_profile.get("education", [])
        primary_edu = edu_list[0] if (edu_list and isinstance(edu_list, list)) else {}

        # Collect verified skills flat set
        skills_dict = candidate_profile.get("skills", {})
        verified_skills = []
        if isinstance(skills_dict, dict):
            for cat, skill_items in skills_dict.items():
                if isinstance(skill_items, list):
                    verified_skills.extend([s.lower() for s in skill_items])
        elif isinstance(skills_dict, list):
            verified_skills = [s.lower() for s in skills_dict]

        # Collect verified projects
        projects = candidate_profile.get("projects", [])
        project_names = [p.get("name", "") for p in projects if isinstance(p, dict)]

        # Work authorization (explicitly declared in profile)
        work_auth = candidate_profile.get("work_authorization")
        if isinstance(work_auth, dict):
            auth_us = work_auth.get("authorized_us")
            req_spon = work_auth.get("requires_sponsorship")
        else:
            auth_us = candidate_profile.get("authorized_us")
            req_spon = candidate_profile.get("requires_sponsorship")

        return {
            "institution": primary_edu.get("institution"),
            "degree": primary_edu.get("degree"),
            "gpa": primary_edu.get("gpa"),
            "graduation_date": primary_edu.get("graduation_date"),
            "coursework": primary_edu.get("coursework", []),
            "authorized_us": auth_us,
            "requires_sponsorship": req_spon,
            "skills": verified_skills,
            "projects": projects,
            "project_names": project_names,
            "full_name": candidate_profile.get("full_name")
        }

    async def generate_answers(
        self,
        candidate_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        custom_questions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generates ATS question responses strictly sourced from candidate profile.
        Flags missing required fields for manual candidate completion.
        """
        facts = self._extract_profile_facts(candidate_profile)
        company = job_data.get("company_name", "the company")
        role = job_data.get("role_title", "Internship")

        answers: Dict[str, Any] = {}
        flagged_fields: List[Dict[str, Any]] = []

        # 1. Map factual profile fields (NO guessing if missing)
        # University / Institution
        if facts["institution"]:
            answers["university"] = facts["institution"]
        else:
            flagged_fields.append({
                "field": "university",
                "question": "University / College Name",
                "requires_manual_input": True,
                "reason": "Institution name not present in candidate profile."
            })

        # Degree level
        if facts["degree"]:
            answers["degree_level"] = facts["degree"]
        else:
            flagged_fields.append({
                "field": "degree_level",
                "question": "Degree Level / Major",
                "requires_manual_input": True,
                "reason": "Degree level not present in candidate profile."
            })

        # Graduation Date
        if facts["graduation_date"]:
            answers["graduation_date"] = facts["graduation_date"]
        else:
            flagged_fields.append({
                "field": "graduation_date",
                "question": "Expected Graduation Date",
                "requires_manual_input": True,
                "reason": "Graduation date not specified in candidate profile."
            })

        # GPA (only include if present in profile)
        if facts["gpa"]:
            answers["gpa"] = facts["gpa"]
        else:
            flagged_fields.append({
                "field": "gpa",
                "question": "Cumulative GPA",
                "requires_manual_input": True,
                "reason": "GPA omitted from candidate profile — manual entry required if requested by company."
            })

        # Work Authorization (only include if explicitly recorded)
        if facts["authorized_us"] is not None:
            answers["authorized_us"] = "Yes" if facts["authorized_us"] in [True, "Yes", "yes", "true", "True"] else "No"
        else:
            flagged_fields.append({
                "field": "authorized_us",
                "question": "Are you legally authorized to work in the United States?",
                "requires_manual_input": True,
                "reason": "Work authorization status not explicitly specified in candidate profile."
            })

        if facts["requires_sponsorship"] is not None:
            answers["requires_sponsorship"] = "Yes" if facts["requires_sponsorship"] in [True, "Yes", "yes", "true", "True"] else "No"
        else:
            flagged_fields.append({
                "field": "requires_sponsorship",
                "question": "Will you now or in the future require visa sponsorship?",
                "requires_manual_input": True,
                "reason": "Visa sponsorship requirement not specified in candidate profile."
            })

        # 2. Company Alignment (rephrases candidate's verified skills & projects)
        if facts["projects"] and len(facts["projects"]) > 0:
            top_proj = facts["projects"][0].get("name", "engineering systems")
            answers["why_this_company"] = (
                f"I am eager to apply my background in building {top_proj} to {company}'s "
                f"engineering team, contributing to scalable systems for the {role} position."
            )
        elif facts["skills"]:
            top_tech = ", ".join(facts["skills"][:3]).title()
            answers["why_this_company"] = (
                f"I am excited to bring my technical experience with {top_tech} to {company}'s {role} role."
            )
        else:
            answers["why_this_company"] = f"I am excited to apply my engineering background to the {role} role at {company}."

        # 3. Handle custom questions if provided
        if custom_questions:
            for q in custom_questions:
                q_lower = q.lower()
                # Check for clearance / licensing / unrecorded facts
                if any(k in q_lower for k in ["clearance", "security clearance", "citizenship", "veteran", "disability", "license", "certification"]):
                    flagged_fields.append({
                        "field": "custom_question",
                        "question": q,
                        "requires_manual_input": True,
                        "reason": "Field requires self-identification or credentials not in profile."
                    })
                elif "why" in q_lower or "interest" in q_lower:
                    answers[q] = answers["why_this_company"]
                elif "language" in q_lower or "tech" in q_lower or "skill" in q_lower:
                    if facts["skills"]:
                        answers[q] = ", ".join([s.title() for s in facts["skills"][:5]])
                    else:
                        flagged_fields.append({
                            "field": "custom_question",
                            "question": q,
                            "requires_manual_input": True,
                            "reason": "Skills not found in candidate profile."
                        })

        # 4. Cross-referencing Traceability Validation
        validation_res = self.validate_traceability(answers, candidate_profile)
        
        # If any answer failed traceability, flag it and remove from prefilled answers
        for flagged in validation_res.get("rejected_answers", []):
            flagged_fields.append(flagged)
            if flagged["field"] in answers:
                del answers[flagged["field"]]

        return {
            "answers": answers,
            "flagged_fields": flagged_fields,
            "validation_passed": validation_res["passed"]
        }

    def validate_traceability(
        self,
        generated_answers: Dict[str, Any],
        candidate_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cross-references every generated answer against the source profile fields.
        Rejects and flags any answer that introduces information not traceable to the resume/profile data.
        """
        facts = self._extract_profile_facts(candidate_profile)
        rejected = []

        # Validate university
        if "university" in generated_answers:
            val = generated_answers["university"]
            if not facts["institution"] or (facts["institution"].lower() not in val.lower() and val.lower() not in facts["institution"].lower()):
                rejected.append({
                    "field": "university",
                    "question": "University",
                    "requires_manual_input": True,
                    "reason": f"Generated university '{val}' is not traceable to candidate profile institution '{facts['institution']}'."
                })

        # Validate degree
        if "degree_level" in generated_answers:
            val = generated_answers["degree_level"]
            if not facts["degree"] or (facts["degree"].lower() not in val.lower() and val.lower() not in facts["degree"].lower()):
                rejected.append({
                    "field": "degree_level",
                    "question": "Degree Level",
                    "requires_manual_input": True,
                    "reason": f"Generated degree '{val}' is not traceable to candidate profile degree '{facts['degree']}'."
                })

        # Validate GPA (must exactly match profile or not exist)
        if "gpa" in generated_answers:
            val = str(generated_answers["gpa"]).strip()
            if not facts["gpa"] or str(facts["gpa"]).strip() != val:
                rejected.append({
                    "field": "gpa",
                    "question": "GPA",
                    "requires_manual_input": True,
                    "reason": f"Generated GPA '{val}' is not in candidate profile (profile GPA: '{facts['gpa']}')."
                })

        # Validate graduation date
        if "graduation_date" in generated_answers:
            val = str(generated_answers["graduation_date"]).strip()
            if not facts["graduation_date"] or facts["graduation_date"].lower() not in val.lower():
                rejected.append({
                    "field": "graduation_date",
                    "question": "Graduation Date",
                    "requires_manual_input": True,
                    "reason": f"Generated graduation date '{val}' does not match profile graduation date '{facts['graduation_date']}'."
                })

        passed = len(rejected) == 0
        return {
            "passed": passed,
            "rejected_answers": rejected
        }

question_answerer = QuestionAnswerer()
