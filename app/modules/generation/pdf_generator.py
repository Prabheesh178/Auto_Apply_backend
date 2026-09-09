import os
from typing import Dict, Any
from jinja2 import Template
from playwright.async_api import async_playwright
from app.config import settings

RESUME_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page {
    size: A4;
    margin: 12mm 14mm 12mm 14mm;
  }
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1a1a1a;
    background: #ffffff;
    font-size: 10.5pt;
    line-height: 1.35;
  }
  .header {
    text-align: center;
    border-bottom: 1.5px solid #222;
    padding-bottom: 6px;
    margin-bottom: 10px;
  }
  .name {
    font-size: 18pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: #0f172a;
  }
  .contact-info {
    font-size: 9pt;
    color: #475569;
    margin-top: 3px;
  }
  .contact-info a {
    color: #2563eb;
    text-decoration: none;
  }
  .section {
    margin-bottom: 9px;
  }
  .section-title {
    font-size: 11pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #1e293b;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 2px;
    margin-bottom: 4px;
  }
  .item-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 10pt;
    font-weight: 600;
    color: #0f172a;
  }
  .item-sub {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    font-size: 9.5pt;
    font-style: italic;
    color: #334155;
    margin-bottom: 2px;
  }
  .date {
    font-weight: 500;
    font-style: normal;
    color: #64748b;
    font-size: 9pt;
  }
  ul {
    margin-left: 14px;
    margin-top: 2px;
    margin-bottom: 4px;
  }
  li {
    font-size: 9.5pt;
    color: #334155;
    margin-bottom: 2px;
    line-height: 1.3;
  }
  .skills-grid {
    font-size: 9.5pt;
    color: #334155;
    line-height: 1.4;
  }
  .skills-label {
    font-weight: 600;
    color: #0f172a;
  }
</style>
</head>
<body>

  <!-- Header -->
  <div class="header">
    <div class="name">{{ candidate.full_name }}</div>
    <div class="contact-info">
      {% if candidate.location %}{{ candidate.location }} • {% endif %}
      {% if candidate.email %}<a href="mailto:{{ candidate.email }}">{{ candidate.email }}</a> • {% endif %}
      {% if candidate.phone %}{{ candidate.phone }} • {% endif %}
      {% if candidate.linkedin_url %}<a href="{{ candidate.linkedin_url }}">LinkedIn</a> • {% endif %}
      {% if candidate.github_url %}<a href="{{ candidate.github_url }}">GitHub</a>{% endif %}
      {% if candidate.portfolio_url %} • <a href="{{ candidate.portfolio_url }}">Portfolio</a>{% endif %}
    </div>
  </div>

  <!-- Education -->
  {% if education %}
  <div class="section">
    <div class="section-title">Education</div>
    {% for edu in education %}
    <div class="item-header">
      <span>{{ edu.institution }}</span>
      <span class="date">{{ edu.graduation_date }}</span>
    </div>
    <div class="item-sub">
      <span>{{ edu.degree }}{% if edu.gpa %} (GPA: {{ edu.gpa }}){% endif %}</span>
      <span>{% if edu.location %}{{ edu.location }}{% endif %}</span>
    </div>
    {% if edu.coursework %}
    <div style="font-size: 9pt; color: #475569; margin-bottom: 2px;">
      <span style="font-weight: 600;">Relevant Coursework:</span> {{ edu.coursework | join(', ') }}
    </div>
    {% endif %}
    {% endfor %}
  </div>
  {% endif %}

  <!-- Technical Skills -->
  {% if skills %}
  <div class="section">
    <div class="section-title">Technical Skills</div>
    <div class="skills-grid">
      {% if skills.languages %}
      <div><span class="skills-label">Languages:</span> {{ skills.languages | join(', ') }}</div>
      {% endif %}
      {% if skills.frameworks %}
      <div><span class="skills-label">Frameworks & Libraries:</span> {{ skills.frameworks | join(', ') }}</div>
      {% endif %}
      {% if skills.infrastructure %}
      <div><span class="skills-label">Infrastructure & Tools:</span> {{ skills.infrastructure | join(', ') }}</div>
      {% endif %}
    </div>
  </div>
  {% endif %}

  <!-- Experience -->
  {% if experience %}
  <div class="section">
    <div class="section-title">Experience</div>
    {% for exp in experience %}
    <div class="item-header">
      <span>{{ exp.title }}</span>
      <span class="date">{{ exp.dates }}</span>
    </div>
    <div class="item-sub">
      <span>{{ exp.company }}</span>
      <span>{{ exp.location }}</span>
    </div>
    {% if exp.highlights %}
    <ul>
      {% for bullet in exp.highlights %}
      <li>{{ bullet }}</li>
      {% endfor %}
    </ul>
    {% endif %}
    {% endfor %}
  </div>
  {% endif %}

  <!-- Projects -->
  {% if projects %}
  <div class="section">
    <div class="section-title">Technical Projects</div>
    {% for proj in projects %}
    <div class="item-header">
      <span>{{ proj.name }} {% if proj.tech_stack %}<span style="font-weight: normal; font-size: 9pt; color: #64748b;">| {{ proj.tech_stack | join(', ') }}</span>{% endif %}</span>
      {% if proj.github %}<span class="date"><a href="{{ proj.github }}" style="color: #2563eb; text-decoration: none; font-size: 8.5pt;">Code Repository</a></span>{% endif %}
    </div>
    {% if proj.description %}
    <ul>
      <li>{{ proj.description }}</li>
      {% if proj.highlights %}
        {% for h in proj.highlights %}
        <li>{{ h }}</li>
        {% endfor %}
      {% endif %}
    </ul>
    {% endif %}
    {% endfor %}
  </div>
  {% endif %}

</body>
</html>
"""

class ResumePdfGenerator:
    def __init__(self):
        self.output_dir = os.path.join(settings.STORAGE_DIR, "resumes")
        os.makedirs(self.output_dir, exist_ok=True)

    def render_html(self, candidate: Dict[str, Any], tailored_data: Dict[str, Any]) -> str:
        """Renders HTML template with tailored candidate data."""
        template = Template(RESUME_HTML_TEMPLATE)

        # Merge master profile and tailored additions
        education = candidate.get("structured_profile", {}).get("education", [])
        if not education and "education" in candidate:
            education = candidate.get("education", [])

        skills = tailored_data.get("skills") or candidate.get("structured_profile", {}).get("skills", {})
        experience = tailored_data.get("experience") or candidate.get("structured_profile", {}).get("experience", [])
        projects = tailored_data.get("projects") or candidate.get("structured_profile", {}).get("projects", [])

        return template.render(
            candidate=candidate,
            education=education,
            skills=skills,
            experience=experience,
            projects=projects
        )

    async def generate_pdf(self, application_id: str, candidate: Dict[str, Any], tailored_data: Dict[str, Any]) -> str:
        """
        Generates a pristine single-page ATS PDF using Playwright headless browser.
        Returns the absolute path of the generated PDF.
        """
        html_content = self.render_html(candidate, tailored_data)
        pdf_path = os.path.abspath(os.path.join(self.output_dir, f"{application_id}_resume.pdf"))

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
                page = await browser.new_page()
                await page.set_content(html_content, wait_until="networkidle")
                await page.pdf(
                    path=pdf_path,
                    format="A4",
                    print_background=True,
                    margin={"top": "10mm", "bottom": "10mm", "left": "12mm", "right": "12mm"}
                )
                await browser.close()
                return pdf_path
        except Exception as e:
            print(f"[ResumePdfGenerator] Error rendering PDF via Playwright: {e}")
            # Fallback: write HTML file
            html_path = pdf_path.replace(".pdf", ".html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            return html_path

resume_pdf_generator = ResumePdfGenerator()
