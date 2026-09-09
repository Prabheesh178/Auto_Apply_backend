import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.settings import SystemSettings
from app.models.candidate import Candidate
from app.models.job import JobListing
from app.models.application import Application
from app.models.activity_log import ActivityLog

async def initialize_seed_data(session: AsyncSession):
    # 1. Check Settings
    stmt = select(SystemSettings).where(SystemSettings.id == 1)
    res = await session.execute(stmt)
    settings = res.scalar_one_or_none()
    if not settings:
        settings = SystemSettings(
            id=1,
            review_before_submit=True,
            is_agent_paused=False,
            target_roles=[
                "Software Engineer Intern",
                "Full Stack Intern",
                "Backend Engineering Intern",
                "Frontend Engineering Intern",
                "AI/ML Research Intern"
            ],
            target_locations=["Remote", "San Francisco, CA", "New York, NY", "Bangalore, India", "Hybrid"],
            min_match_score=75,
            max_daily_applications=15,
            monitored_companies=[
                {"name": "Stripe", "ats": "greenhouse", "slug": "stripe"},
                {"name": "Figma", "ats": "greenhouse", "slug": "figma"},
                {"name": "Notion", "ats": "lever", "slug": "notion"},
                {"name": "Ramp", "ats": "ashby", "slug": "ramp"},
                {"name": "Vercel", "ats": "ashby", "slug": "vercel"},
                {"name": "Coinbase", "ats": "greenhouse", "slug": "coinbase"},
                {"name": "Datadog", "ats": "greenhouse", "slug": "datadog"},
                {"name": "SmartRecruiters Careers", "ats": "smartrecruiters", "slug": "smartrecruiters"}
            ]
        )
        session.add(settings)

    # 2. Check Candidate Profile
    stmt = select(Candidate)
    res = await session.execute(stmt)
    candidate = res.scalars().first()
    if not candidate:
        candidate_id = str(uuid.uuid4())
        candidate = Candidate(
            id=candidate_id,
            full_name="Alex Rivera",
            email="alex.rivera.dev@gmail.com",
            phone="+1 (555) 382-9912",
            location="San Francisco, CA / Remote",
            linkedin_url="https://linkedin.com/in/alexrivera-dev",
            github_url="https://github.com/alexrivera",
            portfolio_url="https://alexrivera.dev",
            raw_resume_text="""ALEX RIVERA
San Francisco, CA | alex.rivera.dev@gmail.com | (555) 382-9912 | github.com/alexrivera

EDUCATION
University of California, Berkeley
B.S. in Computer Science & Data Science (GPA: 3.89/4.0) | Expected May 2026
Coursework: Data Structures, Algorithms, Distributed Systems, Database Systems, Computer Security, Full-Stack Web Architecture.

EXPERIENCE
Software Engineering Intern | CloudScale Labs (May 2024 - Aug 2024)
- Built high-throughput asynchronous ETL pipelines in Python & FastAPI processing 2M+ records daily.
- Designed distributed caching with Redis & PostgreSQL, reducing p99 query latency by 42%.
- Created automated Playwright end-to-end testing suite integrated with GitHub Actions CI/CD.

PROJECTS
- Autonomous Agent Pipeline: Multi-agent orchestration system with Gemini 1.5/2.0 API, React, and vector search.
- FastKV: Embedded key-value store built in Go featuring LSM-trees, write-ahead logging (WAL), and gRPC RPCs.
- Distributed Job Queue: Redis-backed task queue with priority queues, dead-letter exchanges, and worker pools.

SKILLS
Languages: Python, TypeScript, JavaScript, Go, SQL, C++
Frameworks & Tools: FastAPI, React, Next.js, Node.js, PostgreSQL, Docker, Redis, Playwright, Git, Tailwind CSS, GraphQL, AWS
""",
            structured_profile={
                "education": [
                    {
                        "institution": "University of California, Berkeley",
                        "degree": "B.S. in Computer Science & Data Science",
                        "gpa": "3.89/4.0",
                        "graduation_date": "May 2026",
                        "coursework": ["Data Structures", "Algorithms", "Distributed Systems", "Database Systems", "Computer Security"]
                    }
                ],
                "experience": [
                    {
                        "title": "Software Engineering Intern",
                        "company": "CloudScale Labs",
                        "location": "San Francisco, CA",
                        "start_date": "May 2024",
                        "end_date": "Aug 2024",
                        "highlights": [
                            "Built high-throughput asynchronous ETL pipelines in Python & FastAPI processing 2M+ records daily.",
                            "Designed distributed caching with Redis & PostgreSQL, reducing p99 query latency by 42%.",
                            "Created automated Playwright end-to-end testing suite integrated with GitHub Actions CI/CD."
                        ]
                    }
                ],
                "projects": [
                    {
                        "name": "Autonomous Agent Pipeline",
                        "tech_stack": ["Python", "FastAPI", "Gemini API", "React", "PostgreSQL"],
                        "description": "Multi-agent orchestration system with LLM reasoning, async worker queues, and real-time dashboard.",
                        "github": "https://github.com/alexrivera/agent-pipeline"
                    },
                    {
                        "name": "FastKV Distributed Store",
                        "tech_stack": ["Go", "gRPC", "LSM-Tree", "Raft"],
                        "description": "High performance key-value store with write-ahead log and Raft consensus.",
                        "github": "https://github.com/alexrivera/fastkv"
                    }
                ],
                "skills": {
                    "languages": ["Python", "TypeScript", "JavaScript", "Go", "SQL", "C++"],
                    "frameworks": ["FastAPI", "React", "Next.js", "Node.js", "Express", "Tailwind CSS"],
                    "infrastructure": ["PostgreSQL", "Docker", "Redis", "Playwright", "Git", "AWS", "Linux"]
                }
            }
        )
        session.add(candidate)

    # 3. Check Demo Jobs & Applications
    stmt = select(JobListing)
    res = await session.execute(stmt)
    existing_jobs = res.scalars().all()
    
    if not existing_jobs:
        jobs_data = [
            {
                "company_name": "Stripe",
                "role_title": "Software Engineering Intern, Infrastructure",
                "location": "San Francisco, CA / Remote",
                "ats_platform": "greenhouse",
                "job_url": "https://boards.greenhouse.io/stripe/jobs/591024",
                "job_description": "We are looking for Software Engineering Interns to join our core Infrastructure and Developer Productivity teams. You will work on distributed systems, payment rails, and high-reliability APIs.",
                "requirements": ["Proficiency in Python, Go, or Java", "Knowledge of Distributed Systems and Databases", "Strong problem-solving skills"],
                "match_score": 94,
                "match_rationale": "Exceptional fit with candidate's distributed systems coursework, FastAPI backend experience, and high-throughput pipeline background.",
                "app_status": "pending_review",
                "cover_letter": """Dear Stripe Hiring Team,

I am writing to express my enthusiasm for the Software Engineering Intern (Infrastructure) role at Stripe. As a Computer Science student at UC Berkeley with hands-on experience building distributed ETL pipelines and key-value storage engines, I have long admired Stripe's relentless standard for engineering rigor and 99.999% reliability.

During my internship at CloudScale Labs, I engineered asynchronous data pipelines in Python and FastAPI processing over 2M records daily, and architected a Redis/Postgres caching layer that slashed p99 query latency by 42%. Additionally, I designed FastKV, an LSM-tree backed distributed storage engine in Go with Raft consensus.

I would love the opportunity to bring my passion for distributed systems and high-throughput architecture to Stripe's infrastructure team. Thank you for your time and consideration.

Best regards,
Alex Rivera""",
                "form_answers": {
                    "authorized_us": "Yes",
                    "requires_sponsorship": "No",
                    "graduation_date": "May 2026",
                    "preferred_location": "San Francisco, CA / Remote",
                    "why_this_company": "Stripe sets the global gold standard for API design and developer experience. Building fault-tolerant infrastructure at this scale aligns directly with my engineering focus."
                }
            },
            {
                "company_name": "Ramp",
                "role_title": "Full Stack Software Engineer Intern",
                "location": "New York, NY / Remote",
                "ats_platform": "ashby",
                "job_url": "https://jobs.ashbyhq.com/ramp/78b941a3",
                "job_description": "Join Ramp's engineering team to build the financial system of the future. You'll work closely with product and design across our modern Python/React stack.",
                "requirements": ["Experience with Python (FastAPI/Django) and React", "SQL & relational database experience", "Product-minded engineering mindset"],
                "match_score": 91,
                "match_rationale": "Direct stack match with Python/FastAPI backend and React frontend, alongside real-world internship ETL experience.",
                "app_status": "pending_review",
                "cover_letter": """Dear Ramp Engineering Team,

I am excited to apply for the Full Stack Software Engineer Intern role at Ramp. Ramp's incredible velocity in reimagining corporate finance and modern spend management is truly inspiring.

With practical experience across both React/TypeScript frontends and FastAPI/PostgreSQL backends, I thrive at building responsive, high-impact user experiences backed by robust APIs. At CloudScale Labs, I built full-stack workflows with real-time feedback loops and integrated Playwright test suites.

I am eager to contribute to Ramp's velocity and build tools that save companies time and money.

Sincerely,
Alex Rivera""",
                "form_answers": {
                    "authorized_us": "Yes",
                    "requires_sponsorship": "No",
                    "graduation_date": "May 2026",
                    "experience_years": "1 year (Internship + Projects)"
                }
            },
            {
                "company_name": "Figma",
                "role_title": "Frontend Engineering Intern, Web Platforms",
                "location": "San Francisco, CA",
                "ats_platform": "greenhouse",
                "job_url": "https://boards.greenhouse.io/figma/jobs/482019",
                "job_description": "Help us build the next generation of creative tools in the browser. You'll work with WebGL, TypeScript, React, and browser performance optimization.",
                "requirements": ["Strong TypeScript and JavaScript skills", "Understanding of modern DOM, canvas, and browser performance", "Passion for creative UI tooling"],
                "match_score": 86,
                "match_rationale": "Strong frontend fundamentals, React expertise, and browser automation/DOM experience.",
                "app_status": "applied",
                "date_applied": datetime.utcnow() - timedelta(days=2),
                "cover_letter": "Cover letter for Figma Frontend Intern submitted.",
                "form_answers": {"portfolio": "https://alexrivera.dev"}
            },
            {
                "company_name": "Notion",
                "role_title": "Backend Engineering Intern, Core Infrastructure",
                "location": "San Francisco, CA / Hybrid",
                "ats_platform": "lever",
                "job_url": "https://jobs.lever.co/notion/c1992-intern",
                "job_description": "We are seeking a Backend Engineering Intern to help scale Notion's core collaborative data engine and block infrastructure.",
                "requirements": ["Experience with TypeScript/Node.js or Python", "Database fundamentals (PostgreSQL)", "Interest in collaborative real-time editing"],
                "match_score": 89,
                "match_rationale": "Strong alignment with candidate's backend data modeling and distributed caching experience.",
                "app_status": "interview",
                "date_applied": datetime.utcnow() - timedelta(days=5),
                "last_reply_snippet": "Hi Alex, thank you for applying! We were very impressed with your background and would love to invite you to a 45-minute technical screen next week.",
                "last_reply_at": datetime.utcnow() - timedelta(days=1),
                "cover_letter": "Cover letter for Notion Backend Intern submitted.",
                "form_answers": {"heard_about_us": "University Career Fair"}
            },
            {
                "company_name": "Datadog",
                "role_title": "Software Engineering Intern, APM & Tracing",
                "location": "New York, NY",
                "ats_platform": "greenhouse",
                "job_url": "https://boards.greenhouse.io/datadog/jobs/339100",
                "job_description": "Work on observability infrastructure processing trillions of events per day. Gain deep experience with telemetry, metrics pipelines, and distributed tracing.",
                "requirements": ["Python or Go programming", "Linux fundamentals", "Passion for high scale systems"],
                "match_score": 88,
                "match_rationale": "High relevance to candidate's systems coursework, Go key-value store, and latency optimization metrics.",
                "app_status": "applied",
                "date_applied": datetime.utcnow() - timedelta(days=3),
                "cover_letter": "Cover letter for Datadog Intern submitted.",
                "form_answers": {"work_auth": "Authorized"}
            },
            {
                "company_name": "Coinbase",
                "role_title": "Software Engineer Intern, Crypto Platforms",
                "location": "Remote",
                "ats_platform": "greenhouse",
                "job_url": "https://boards.greenhouse.io/coinbase/jobs/920194",
                "job_description": "Build decentralized and high-security financial backend services powering millions of customer transactions.",
                "requirements": ["Computer Science major", "Knowledge of algorithms, cryptography, or databases", "High security mindset"],
                "match_score": 79,
                "match_rationale": "Good match with CS foundation, database coursework, and security basics.",
                "app_status": "rejected",
                "date_applied": datetime.utcnow() - timedelta(days=7),
                "last_reply_snippet": "Thank you for your interest in Coinbase. While your background is impressive, we have chosen to move forward with candidates whose experience more closely matches this role.",
                "last_reply_at": datetime.utcnow() - timedelta(days=2),
                "cover_letter": "Cover letter for Coinbase Intern submitted.",
                "form_answers": {}
            }
        ]

        for item in jobs_data:
            job_id = str(uuid.uuid4())
            job = JobListing(
                id=job_id,
                company_name=item["company_name"],
                role_title=item["role_title"],
                location=item["location"],
                ats_platform=item["ats_platform"],
                job_url=item["job_url"],
                ats_job_id=str(uuid.uuid4())[:8],
                job_description=item["job_description"],
                requirements=item["requirements"],
                is_internship=True,
                match_score=item["match_score"],
                match_rationale=item["match_rationale"],
                discovered_at=datetime.utcnow() - timedelta(hours=12)
            )
            session.add(job)

            app_id = str(uuid.uuid4())
            app = Application(
                id=app_id,
                job_id=job_id,
                candidate_id=candidate.id if candidate else candidate_id,
                status=item["app_status"],
                cover_letter_text=item.get("cover_letter"),
                form_answers=item.get("form_answers", {}),
                tailored_resume_json={
                    "selected_bullets": [
                        "Built high-throughput asynchronous ETL pipelines in Python & FastAPI processing 2M+ records daily.",
                        "Designed distributed caching with Redis & PostgreSQL, reducing p99 query latency by 42%.",
                        "Created automated Playwright end-to-end testing suite integrated with GitHub Actions CI/CD."
                    ],
                    "target_skills": ["Python", "FastAPI", "Distributed Systems", "PostgreSQL", "Playwright"]
                },
                date_applied=item.get("date_applied"),
                last_reply_snippet=item.get("last_reply_snippet"),
                last_reply_at=item.get("last_reply_at")
            )
            session.add(app)

        # 4. Activity Logs
        logs = [
            ("SUCCESS", "System", "Auto-Apply backend daemon initialized and connected to database."),
            ("INFO", "Discovery", "Discovered 6 new internship postings across Greenhouse, Lever, and Ashby."),
            ("INFO", "Matcher", "Evaluated candidates against Stripe Infrastructure Intern (Match Score: 94%)."),
            ("INFO", "Tailorer", "Generated tailored cover letter & resume emphasis for Stripe application."),
            ("WARN", "ReviewQueue", "Review-before-submit gate active. 2 applications queued for candidate approval."),
            ("SUCCESS", "Watcher", "Gmail watcher synced: Received interview invitation from Notion.")
        ]
        for level, comp, msg in logs:
            log = ActivityLog(
                level=level,
                component=comp,
                message=msg,
                metadata_json={"seed": True},
                created_at=datetime.utcnow() - timedelta(minutes=15)
            )
            session.add(log)

    await session.commit()
