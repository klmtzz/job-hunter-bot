import os
from dataclasses import dataclass, field
from typing import List, Set
from dotenv import load_dotenv

load_dotenv()

@dataclass
class BotConfig:
    # Telegram API settings
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    telegram_chat_id: int = field(default_factory=lambda: int(os.getenv("TELEGRAM_CHAT_ID", "0")))
    poll_interval_minutes: int = field(default_factory=lambda: int(os.getenv("POLL_INTERVAL_MINUTES", "30")))
    
    # LLM API configuration for semantic evaluation
    llm_api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4-turbo"))
    
    # Job filtering criteria
    min_score_threshold: int = 10
    max_job_age_days: int = 14
    
    # Keywords for parsing & heuristics scoring
    must_have_stack: List[str] = field(default_factory=lambda: [
        "python", "fastapi", "asyncio", "aiogram", "postgresql", "docker"
    ])
    
    nice_to_have_stack: List[str] = field(default_factory=lambda: [
        "redis", "sqlalchemy", "playwright", "scraping", "web3", "langchain", "llama-index"
    ])
    
    hard_skip_keywords: List[str] = field(default_factory=lambda: [
        "senior", "sr.", "lead", "5+ years", "10+ years", "unpaid", "c++", "java", "net"
    ])
    
    # Target roles for scoring boosts
    target_roles: List[str] = field(default_factory=lambda: [
        "junior", "intern", "trainee", "associate", "automation engineer"
    ])

# Global configuration instance
config = BotConfig()
