import logging
import html
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import config
from database import DatabaseManager
from scorer import JobScorer
from parsers import ALL_PARSERS

logger = logging.getLogger(__name__)

# Core instances loaded in bot runtime
db_manager = DatabaseManager()
scorer = JobScorer()

def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    def is_admin(msg: Message) -> bool:
        """Enforces admin access locks using authorized chat IDs."""
        return msg.chat.id == config.telegram_chat_id

    @dp.message(CommandStart())
    async def start_handler(msg: Message):
        if not is_admin(msg):
            return
        
        await msg.answer(
            "🚀 <b>AI-Driven Autonomous Job Search & Applications Orchestrator</b>\n\n"
            f"Active Parsers: <code>{len(ALL_PARSERS)}</code>\n"
            f"Configured scoring threshold: <b>{config.min_score_threshold}</b>\n"
            f"Time limit: <b>{config.max_job_age_days} days</b>\n\n"
            "<b>Bot Commands:</b>\n"
            "/run — Perform crawling cycle manually\n"
            "/top — Show top jobs matching criteria\n"
            "/stats — Display crawler stats\n"
            "/cover — Generate CV cover letter template"
        )

    @dp.message(Command("run"))
    async def run_handler(msg: Message):
        if not is_admin(msg):
            return
            
        await msg.answer("🔄 Starting manual job crawler cycle...")
        
        scraped_count = 0
        added_count = 0

        for parser in ALL_PARSERS:
            jobs = await parser.safe_fetch()
            scraped_count += len(jobs)
            for job in jobs:
                # Calculate scores
                h_score, reasons = scorer.heuristic_evaluate(job)
                
                # Check for hard skip values
                if h_score < 0:
                    continue

                # Run advanced LLM evaluation
                final_score, analysis_msg = await scorer.llm_evaluate(job, h_score)
                reasons.append(analysis_msg)

                # Persist to database
                inserted = await db_manager.insert_job(job, final_score, reasons)
                if inserted:
                    added_count += 1
                    # Notify admin if score passes threshold
                    if final_score >= config.min_score_threshold:
                        alert = (
                            f"🔥 <b>Tier-1 Lead Found ({final_score} points)</b>\n"
                            f"<b>Title:</b> {html.escape(job['title'])}\n"
                            f"<b>Company:</b> {html.escape(job['company'])}\n"
                            f"<b>Location:</b> {html.escape(job['location'])}\n"
                            f"<b>Salary:</b> {html.escape(job['salary'])}\n"
                            f"<b>Reasoning:</b> {html.escape(', '.join(reasons))}\n\n"
                            f"🔗 <a href='{job['url']}'>Apply Here</a>"
                        )
                        await msg.bot.send_message(
                            config.telegram_chat_id, 
                            alert, 
                            disable_web_page_preview=True
                        )

        await msg.answer(
            f"✅ <b>Cycle Completed.</b>\n"
            f"• Scraped: <code>{scraped_count}</code> postings\n"
            f"• Inserted to DB: <code>{added_count}</code> new posts"
        )

    @dp.message(Command("top"))
    async def top_handler(msg: Message):
        if not is_admin(msg):
            return
            
        jobs = await db_manager.get_top_jobs(limit=10, min_score=config.min_score_threshold)
        if not jobs:
            await msg.answer("No high-quality leads found in the database yet.")
            return

        response = ["📊 <b>Top Job Recommendations:</b>\n"]
        for idx, job in enumerate(jobs, 1):
            response.append(
                f"{idx}. <b>{html.escape(job['title'])}</b> at {html.escape(job['company'])} (Score: {job['score']})\n"
                f"   🔗 <a href='{job['url']}'>Link</a> | Reasons: {html.escape(job['reasons'])}\n"
            )
            
        await msg.answer("\n".join(response), disable_web_page_preview=True)

    @dp.message(Command("stats"))
    async def stats_handler(msg: Message):
        if not is_admin(msg):
            return
            
        stats = await db_manager.get_stats()
        await msg.answer(
            "📊 <b>Crawler Statistics:</b>\n\n"
            f"• Total jobs in database: <code>{stats['total_scraped']}</code>\n"
            f"• Jobs passing score criteria: <code>{stats['passed_filters']}</code>\n"
            f"• Breakdowns by scraper source:\n" + 
            "\n".join([f"  - <i>{source}</i>: {count}" for source, count in stats['by_source'].items()])
        )

    @dp.message(Command("cover"))
    async def cover_handler(msg: Message):
        if not is_admin(msg):
            return

        # Template showing clean CV generator functionality
        cover_letter = (
            "Subject: Software Engineer Application\n\n"
            "Dear Hiring Team,\n\n"
            "I am writing to express my strong interest in joining your team as a software engineer. "
            "With my background in Python development, FastAPI web services, and task automation, "
            "I build resilient backend products and workflows. "
            "My experience deploying database-backed services in containerized Docker systems "
            "fits closely with clean coding practices.\n\n"
            "I actively leverage modern workflows, incorporating AI-agents and automated scripts "
            "to scale code coverage and product cycles.\n\n"
            "I'm eager to discuss my skills during an interview or tackle any test assignments you provide.\n\n"
            "Best regards,\n"
            "Candidate"
        )
        await msg.answer(f"📝 <b>Generated Cover Letter:</b>\n\n<pre>{cover_letter}</pre>")

    return dp

def build_bot() -> Bot:
    if not config.bot_token:
        raise ValueError("BOT_TOKEN environment variable is not set")
    return Bot(
        token=config.bot_token, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
