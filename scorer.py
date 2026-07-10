import re
import json
import logging
from typing import Dict, Any, Tuple, List
import httpx
from config import config

logger = logging.getLogger(__name__)

class JobScorer:
    """Evaluates and filters job postings using keyword heuristics and LLM semantic analysis."""

    def __init__(self):
        # Pre-compile regex for performance
        self.skip_patterns = [re.compile(rf"\b{word}\b", re.IGNORECASE) for word in config.hard_skip_keywords]
        self.target_patterns = [re.compile(rf"\b{word}\b", re.IGNORECASE) for word in config.target_roles]

    def heuristic_evaluate(self, job: Dict[str, Any]) -> Tuple[int, List[str]]:
        """
        Runs fast, deterministic keyword-based heuristics on job content.
        Returns a score and a list of reasoning tags.
        """
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()
        full_text = f"{title} {description}"
        
        reasons = []
        score = 0

        # 1. Check hard skips (immediate rejection if pattern matches)
        for pattern in self.skip_patterns:
            match = pattern.search(full_text)
            if match:
                return -100, [f"Hard-skip keyword match: '{match.group(0)}'"]

        # 2. Score must-have technologies
        must_have_hits = [tech for tech in config.must_have_stack if tech in full_text]
        if must_have_hits:
            boost = len(must_have_hits) * 3
            score += boost
            reasons.append(f"+{boost} must-have tech: {must_have_hits}")

        # 3. Score nice-to-have technologies
        nice_to_have_hits = [tech for tech in config.nice_to_have_stack if tech in full_text]
        if nice_to_have_hits:
            boost = len(nice_to_have_hits) * 1
            score += boost
            reasons.append(f"+{boost} nice-to-have tech: {nice_to_have_hits}")

        # 4. Score target roles (e.g., junior, intern) in title
        for pattern in self.target_patterns:
            if pattern.search(title):
                score += 5
                reasons.append(f"+5 target role in title: '{pattern.pattern}'")
                break

        return score, reasons

    async def llm_evaluate(self, job: Dict[str, Any], heuristic_score: int) -> Tuple[int, str]:
        """
        Uses an LLM agent model to evaluate a job post's fit based on developer's profile.
        This provides semantic understanding beyond simple keyword matches.
        """
        if not config.llm_api_key:
            # Fallback if no API key is configured
            return heuristic_score, "LLM scoring skipped (no API key)"

        prompt = f"""
You are an expert AI job recruiter agent. Evaluate the following job posting against the target candidate profile.

Candidate Profile:
- Skills: Python (advanced), FastAPI, Asyncio, SQL/PostgreSQL, Docker, Git.
- Seeking: Junior/Intern/Associate software engineer roles or automated QA roles.
- Prefers: Remote-first work, Web3/cryptocurrency domains, clean engineering practices.

Job Posting:
Title: {job.get('title')}
Company: {job.get('company')}
Description: {job.get('description', '')[:2000]}

Heuristic Score Calculated: {heuristic_score}

Return a JSON object containing:
1. "score": An integer from 1 to 20 representing the alignment (20 being perfect match).
2. "fit_analysis": A single sentence explanation of why this job fits or doesn't fit the candidate.

Example JSON output format:
{{"score": 14, "fit_analysis": "Excellent stack alignment with Python and FastAPI, though requires basic cloud experience."}}
"""
        headers = {
            "Authorization": f"Bearer {config.llm_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.llm_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.llm_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                content = result['choices'][0]['message']['content']
                parsed = json.loads(content)
                
                final_score = int(parsed.get("score", heuristic_score))
                analysis = parsed.get("fit_analysis", "Successfully analyzed.")
                return final_score, f"LLM Match: {analysis}"
                
        except Exception as e:
            logger.warning(f"LLM scoring failed due to error: {e}. Falling back to heuristics.")
            return heuristic_score, f"Heuristic scoring fallback (LLM failed: {str(e)})"
