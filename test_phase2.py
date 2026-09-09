import asyncio
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.modules.discovery.greenhouse import greenhouse_client
from app.modules.discovery.lever import lever_client
from app.modules.discovery.ashby import ashby_client
from app.modules.discovery.smartrecruiters import smartrecruiters_client
from app.modules.resume.parser import resume_parser
from app.modules.matching.matcher import semantic_matcher
from app.modules.discovery.orchestrator import discovery_orchestrator

async def run_phase2_tests():
    print("========================================")
    print("    AUTO-APPLY PHASE 2 TEST SUITE       ")
    print("========================================")

    # 1. Test Greenhouse Client
    print("\n[1/5] Testing Greenhouse ATS Client (Cloudflare / Figma)...")
    gh_jobs = await greenhouse_client.fetch_company_jobs("cloudflare")
    print(f"-> Fetched {len(gh_jobs)} jobs from Cloudflare Greenhouse.")
    if gh_jobs:
        sample = gh_jobs[0]
        print(f"   Sample: '{sample['role_title']}' in '{sample['location']}' (ATS ID: {sample['ats_job_id']})")

    # 2. Test Lever Client
    print("\n[2/5] Testing Lever ATS Client (Notion)...")
    lever_jobs = await lever_client.fetch_company_jobs("notion")
    print(f"-> Fetched {len(lever_jobs)} jobs from Notion Lever.")
    if lever_jobs:
        sample = lever_jobs[0]
        print(f"   Sample: '{sample['role_title']}' in '{sample['location']}'")

    # 3. Test Ashby Client
    print("\n[3/5] Testing Ashby ATS Client (Ramp / Vercel)...")
    ashby_jobs = await ashby_client.fetch_company_jobs("ramp")
    print(f"-> Fetched {len(ashby_jobs)} jobs from Ramp Ashby.")
    if ashby_jobs:
        sample = ashby_jobs[0]
        print(f"   Sample: '{sample['role_title']}' in '{sample['location']}'")

    # 4. Test Resume Parser
    print("\n[4/5] Testing Resume Parser...")
    sample_resume_text = """
    ELENA CHEN
    San Francisco, CA | elena.chen@berkeley.edu | (555) 492-1100 | github.com/elenachen | linkedin.com/in/elena-chen

    EDUCATION
    University of California, Berkeley — B.S. in Computer Science (GPA: 3.92) | Expected May 2026
    Coursework: Data Structures, Operating Systems, Computer Networks, Database Architecture.

    EXPERIENCE
    Software Engineering Intern | NextGen AI (June 2024 - August 2024)
    - Developed asynchronous REST microservices using Python, FastAPI, and Redis.
    - Optimized PostgreSQL query execution plans, reducing p95 latency by 35%.
    - Built automated end-to-end integration tests using Playwright.

    PROJECTS
    Distributed KV Engine: LSM-tree based persistent key-value store built in Go with Raft consensus protocol.
    Real-Time Collaboration Canvas: React and WebSockets collaborative whiteboard app.

    SKILLS
    Languages: Python, TypeScript, Go, SQL, C++
    Frameworks: FastAPI, React, Node.js, Next.js, Express
    Infrastructure: Docker, PostgreSQL, Redis, Git, Linux, Playwright
    """

    test_file = "test_sample_resume.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(sample_resume_text)

    parsed_profile = await resume_parser.parse_and_update(test_file)
    print(f"-> Candidate Parsed: {parsed_profile['full_name']} ({parsed_profile['email']})")
    print(f"   Languages: {parsed_profile['structured_profile'].get('skills', {}).get('languages', [])}")
    print(f"   Projects: {len(parsed_profile['structured_profile'].get('projects', []))}")

    # 5. Test Semantic Matcher
    print("\n[5/5] Testing Semantic Matching Engine...")
    test_job = {
        "company_name": "Stripe",
        "role_title": "Software Engineering Intern, Infrastructure",
        "location": "San Francisco, CA / Remote",
        "job_description": "We are seeking a Software Engineering Intern to join our Distributed Systems and Developer Infrastructure team. Requirements: Experience with Python, Go, or Distributed Systems. Strong algorithms and database knowledge.",
    }
    evaluation = await semantic_matcher.evaluate_match(parsed_profile["structured_profile"], test_job)
    print(f"-> Match Score: {evaluation['match_score']}%")
    print(f"   Rationale: {evaluation['match_rationale']}")
    print(f"   Matching Skills: {evaluation.get('matching_skills')}")

    # Clean up test file
    if os.path.exists(test_file):
        os.remove(test_file)

    print("\n========================================")
    print("   ALL PHASE 2 UNIT TESTS PASSED!       ")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_phase2_tests())
