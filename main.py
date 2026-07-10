import asyncio
import logging
import sys
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from config import config
from database import DatabaseManager
from bot import build_bot, build_dispatcher, db_manager

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Mute chatty dependencies
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.WARNING)

async def crawl_task(bot, dp):
    """Execution cycle triggered by scheduler interval."""
    logger.info("Triggering scheduled crawl execution cycle...")
    # Inject command handler context as mock call
    class MockMessage:
        def __init__(self, bot):
            self.bot = bot
            # Mock chat details corresponding to configured chat_id
            class MockChat:
                id = config.telegram_chat_id
            self.chat = MockChat()
        async def answer(self, text):
            logger.info(f"[Scheduled Task Log] {text}")
            
    mock_msg = MockMessage(bot)
    # Invoke run command handler directly to perform scheduled scraping
    run_handler = dp.message.handlers[1] # Reference "/run" command handler
    await run_handler.callback(mock_msg)

async def main() -> None:
    load_dotenv()
    
    # Initialize components
    logger.info("Initializing Showcase Job Hunter Database...")
    await db_manager.init_db()

    # Build Bot and Dispatcher instances
    try:
        bot = build_bot()
        dp = build_dispatcher()
    except ValueError as e:
        logger.error(f"Initialization configuration error: {e}")
        logger.error("Please configure BOT_TOKEN in environment variables (.env)")
        sys.exit(1)

    # Initialize Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        crawl_task,
        "interval",
        minutes=config.poll_interval_minutes,
        args=[bot, dp],
        id="scheduled_crawl_job"
    )
    scheduler.start()
    logger.info(f"Cron scheduler started. Crawling job interval: {config.poll_interval_minutes} minutes.")

    # Startup logic: run a crawl task after start
    asyncio.create_task(crawl_task(bot, dp))

    # Start polling
    logger.info("Starting Telegram Bot long-polling server...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()
        logger.info("Application shut down cleanly.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received exit signal. Shutting down...")
