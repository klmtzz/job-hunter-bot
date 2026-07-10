import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from .base import BaseParser

logger = logging.getLogger(__name__)

class ExampleParser(BaseParser):
    """
    Showcase parser template.
    Demonstrates scraping, data sanitation, and structured output formatting.
    """
    name = "example_jobboard"
    base_url = "https://example.com/jobs"

    async def fetch(self) -> List[Dict[str, Any]]:
        # Mocking HTML response for demonstration
        html = """
        <div class="job-card" id="job_101">
            <a class="job-title" href="/jobs/python-engineer-101">Async Python Developer (FastAPI)</a>
            <span class="company-name">FastTech Labs</span>
            <span class="salary-range">$70k - $90k</span>
            <span class="location">Remote (EU/US timezone)</span>
            <p class="description">We are seeking a Junior/Mid Python Developer. Tech: FastAPI, Docker, PostgreSQL.</p>
        </div>
        <div class="job-card" id="job_102">
            <a class="job-title" href="/jobs/senior-dev-102">Senior Lead Devops</a>
            <span class="company-name">Legacy Enterprise Inc</span>
            <span class="salary-range">$150k - $200k</span>
            <span class="location">New York, NY</span>
            <p class="description">Experienced DevOps Engineer with 10+ years experience in Kubernetes, C++, Java.</p>
        </div>
        """
        
        # In production, you would fetch the live page like this:
        # html = await self._get(self.base_url)
        
        return self._parse_html(html)

    def _parse_html(self, html_content: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html_content, "html.parser")
        jobs = []

        for card in soup.select(".job-card"):
            title_el = card.select_one(".job-title")
            if not title_el:
                continue

            href = title_el.get("href", "")
            title = title_el.get_text(strip=True)
            external_id = re.sub(r"\D", "", href) or href.split("-")[-1]

            company_el = card.select_one(".company-name")
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            salary_el = card.select_one(".salary-range")
            salary = salary_el.get_text(strip=True) if salary_el else ""

            location_el = card.select_one(".location")
            location = location_el.get_text(strip=True) if location_el else "Remote"

            desc_el = card.select_one(".description")
            description = desc_el.get_text(strip=True) if desc_el else ""

            jobs.append({
                "source": self.name,
                "external_id": external_id,
                "title": title,
                "company": company,
                "url": f"https://example.com{href}" if href.startswith("/") else href,
                "location": location,
                "salary": salary,
                "description": description,
                "posted_at": "Today"
            })

        return jobs
