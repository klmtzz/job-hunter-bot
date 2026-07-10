# 🤖 Autonomous AI-Agent Job Search Orchestrator

An advanced, production-grade asynchronous pipeline designed to crawl job boards, execute concurrent multi-source parsing, evaluate positions using semantic LLM-based analysis, and dispatch notifications to Telegram channels.

This project is a showcase of high-quality **asynchronous Python architecture**, demonstrating clean software engineering, database optimizations, and integrations with Large Language Models.

---

## 🏗️ Architecture & Pipeline Flow

The orchestrator operates on a modular pipelines model, separating concerns between asynchronous fetching, heuristic filtering, cognitive evaluation, and notification delivery.

```mermaid
graph TD
    A[Scheduler / Trigger] --> B[Crawler Engine]
    B -->|Concurrent Workers| C1[Web3.Career Parser]
    B -->|Concurrent Workers| C2[RemoteOK Parser]
    B -->|Concurrent Workers| C3[HackerNews Parser]
    
    C1 & C2 & C3 -->|Raw Job Data| D[Deduplication Layer]
    D -->|New Listings Only| E[Scoring & Evaluation Engine]
    
    E -->|Fast Regex Filters| F[Heuristic Filter]
    F -->|Fail| G[Filtered Out]
    F -->|Pass| H[Semantic LLM Agent]
    
    H -->|Score & Analysis JSON| I[Database Manager SQLite]
    I -->|Passed Threshold| J[Notification Service]
    J -->|Telegram Push Alert| K[Telegram Admin Client]
```

---

## ⚡ Core Engineering Highlights

### 1. High-Performance Asynchronous Concurrency
* Utilizes **asyncio** and **httpx** to perform concurrent page scrapes across 15+ job boards.
* Employs **semaphores** to enforce strict rate-limiting, preventing IP blacklists.
* Implements **exponential backoff retry policies** to gracefully handle network issues and rate limits.

### 2. Multi-Tier Intelligent Scoring
* **Heuristics Tier:** High-performance pre-compiled regex matching filters out mismatched positions (e.g., senior roles, outdated stack) in milliseconds, saving LLM tokens.
* **Cognitive Semantic Tier:** Jobs that pass heuristics are processed by an LLM-Agent (OpenAI/Fireworks APIs) using custom prompt templates to score alignment and compile analytical feedback.

### 3. Database Layer Optimizations
* Implements an asynchronous wrapper around SQLite via **aiosqlite**, featuring parameterized queries to prevent SQL injections.
* Custom database indices (`idx_jobs_score`, `idx_jobs_source_ext`) ensure high-speed querying of top-scoring leads even as the database scales.

### 4. Advanced Telegram MVC Controls
* Developed using **aiogram v3** (Model-View-Controller framework).
* Integrates custom commands `/run` (force scraping cycles), `/top` (list recommendations), `/stats` (analytics), and `/cover` (auto-generate cover letters customized to specific job descriptions).

---

## 📂 Codebase Overview

```
job-hunter-bot-showcase/
├── main.py              # Orchestration entry point and APScheduler
├── config.py            # Strong-typed settings schema (dataclasses + python-dotenv)
├── database.py          # Asynchronous parameterized database wrapper (aiosqlite)
├── scorer.py            # Keyword heuristic and LLM semantic match scoring engines
├── bot.py               # MVC architecture Telegram Bot command handlers (aiogram v3)
├── requirements.txt     # Dependency locklist
└── parsers/             # Concurrent scraping microservices
    ├── base.py          # Abstract scraper class with retry logic & request sessions
    └── example_parser.py# Extensible BeautifulSoup HTML scraping subclass
```

---

## 🚀 Getting Started

### 📋 Prerequisites
* Python 3.10+
* A Telegram Bot Token (obtained from `@BotFather`)
* An OpenAI-compatible LLM API Key (optional, for semantic analysis)

### 🛠️ Installation
1. Clone the showcase repository:
   ```bash
   git clone https://github.com/klmtzz/job-hunter-bot-showcase.git
   cd job-hunter-bot-showcase
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create and populate environment variables `.env`:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   POLL_INTERVAL_MINUTES=30
   
   # Optional: LLM Semantic Scoring Configuration
   LLM_API_KEY=your_llm_api_key
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_MODEL=gpt-4-turbo
   ```

5. Run the orchestrator:
   ```bash
   python main.py
   ```

---

## 📝 Design Patterns Demonstrated
* **Abstract Factory / Base Template:** Used in `BaseParser` to enforce schema constraints on scraper subclasses.
* **Singleton / Global Config:** Configurations are initialized once in `config.py` and exported cleanly.
* **Separation of Concerns (SoC):** Database manipulation, scoring algorithms, and messaging protocols are decoupled and isolated.
