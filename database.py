import logging
import sqlite3
from typing import List, Dict, Any, Tuple
import aiosqlite

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Asynchronous manager for SQLite storage using aiosqlite."""
    
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path

    async def init_db(self) -> None:
        """Initializes database tables and creates indexes if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    url TEXT NOT NULL,
                    location TEXT,
                    salary TEXT,
                    description TEXT,
                    posted_at TEXT,
                    score INTEGER DEFAULT 0,
                    reasons TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source, external_id)
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source_ext ON jobs(source, external_id)")
            await db.commit()
            logger.info("Database initialized successfully.")

    async def insert_job(self, job_data: Dict[str, Any], score: int, reasons: List[str]) -> bool:
        """
        Inserts a new job listing.
        Returns True if inserted, False if it already exists (violating UNIQUE constraint).
        """
        reasons_str = ", ".join(reasons)
        query = """
            INSERT OR IGNORE INTO jobs 
            (source, external_id, title, company, url, location, salary, description, posted_at, score, reasons)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            job_data.get("source"),
            job_data.get("external_id"),
            job_data.get("title"),
            job_data.get("company"),
            job_data.get("url"),
            job_data.get("location", ""),
            job_data.get("salary", ""),
            job_data.get("description", ""),
            job_data.get("posted_at", ""),
            score,
            reasons_str
        )
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.rowcount > 0

    async def get_top_jobs(self, limit: int = 10, min_score: int = 10) -> List[Dict[str, Any]]:
        """Retrieves top scoring jobs exceeding the threshold."""
        query = """
            SELECT source, external_id, title, company, url, salary, score, reasons, posted_at
            FROM jobs
            WHERE score >= ?
            ORDER BY score DESC, created_at DESC
            LIMIT ?
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, (min_score, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_stats(self) -> Dict[str, Any]:
        """Gathers system statistics regarding scraped jobs."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM jobs") as cursor:
                total_jobs = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COUNT(*) FROM jobs WHERE score >= 10") as cursor:
                passed_jobs = (await cursor.fetchone())[0]
                
            async with db.execute("SELECT source, COUNT(*) FROM jobs GROUP BY source") as cursor:
                source_counts = await cursor.fetchall()
                
        return {
            "total_scraped": total_jobs,
            "passed_filters": passed_jobs,
            "by_source": {source: count for source, count in source_counts}
        }
