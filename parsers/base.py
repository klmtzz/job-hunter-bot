import asyncio
import logging
from typing import List, Dict, Any
import httpx

logger = logging.getLogger(__name__)

class BaseParser:
    """
    Abstract Base Class for all crawlers/scrapers.
    Provides standardized, resilient HTTP request clients with retry policies.
    """
    name: str = "base"
    base_url: str = ""

    async def fetch(self) -> List[Dict[str, Any]]:
        """Parses the site and returns list of job dictionary objects."""
        raise NotImplementedError("Each parser subclass must implement fetch()")

    async def _get(self, url: str, headers: Dict[str, str] = None, retries: int = 3, **kwargs) -> str:
        """Helper method that performs HTTP GET requests with exponential backoffs."""
        default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        if headers:
            default_headers.update(headers)
            
        timeout = httpx.Timeout(10.0, connect=5.0)

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    response = await client.get(url, headers=default_headers, **kwargs)
                    response.raise_for_status()
                    return response.text
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                if attempt == retries - 1:
                    logger.error(f"Failed fetching {url} after {retries} attempts: {e}")
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Error fetching {url} (Attempt {attempt+1}/{retries}). Retrying in {wait_time}s... Error: {e}")
                await asyncio.sleep(wait_time)
        return ""

    async def safe_fetch(self) -> List[Dict[str, Any]]:
        """Invokes subclass fetch with safety wrappers preventing main thread disruptions."""
        try:
            results = await self.fetch()
            logger.info(f"[{self.name}] Parser completed. Scraped {len(results)} items.")
            return results
        except Exception as e:
            logger.exception(f"[{self.name}] Parser failed during execution: {e}")
            return []
