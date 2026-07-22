# 🤖 Autonomous Job Search Orchestrator & Data Pipeline

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![AsyncIO](https://img.shields.io/badge/async-asyncio%20%7C%20httpx-green.svg)](https://docs.python.org/3/library/asyncio.html)
[![Aiogram v3](https://img.shields.io/badge/telegram-aiogram%20v3-blue.svg)](https://docs.aiogram.dev/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced, production-grade asynchronous pipeline designed to crawl job boards, execute concurrent multi-source parsing, evaluate positions using rule-based scoring engines, and dispatch real-time notifications to Telegram channels.

This project is a showcase of high-quality **asynchronous Python architecture**, demonstrating clean software engineering, database optimizations, containerized deployment, and resilient web scraping patterns.

---

## 🏗️ Architecture & Pipeline Flow

The orchestrator operates on a modular pipeline model, separating concerns between asynchronous fetching, heuristic filtering, rule evaluation, and notification delivery.

```mermaid
graph TD
    A[Scheduler / Trigger] --> B[Crawler Engine]
    B -->|Concurrent Workers| C1[Web3.Career Parser]
    B -->|Concurrent Workers| C2[RemoteOK Parser]
    B -->|Concurrent Workers| C3[HackerNews Parser]
    
    C1 & C2 & C3 -->|Raw Job Data| D[Deduplication Layer]
    D -->|New Listings Only| E[Scoring & Evaluation Engine]
    
    E -->|Pre-compiled Regex Filters| F[Heuristic Filter]
    F -->|Fail| G[Filtered Out]
    F -->|Pass| H[Match & Score Engine]
    
    H -->|Score & Analysis JSON| I[Database Manager SQLite]
    I -->|Passed Threshold| J[Notification Service]
    J -->|Telegram Push Alert| K[Telegram Admin Client]
```

---

## ⚡ Core Engineering Highlights

### 1. High-Performance Asynchronous Concurrency
* Utilizes **asyncio** and **httpx** to perform concurrent page scrapes across multiple job boards.
* Employs **semaphores** to enforce strict rate-limiting and avoid IP blacklisting.
* Implements **exponential backoff retry policies** to gracefully handle network errors and rate limits.

### 2. Multi-Tier Rule & Scoring Engine
* **Heuristics Tier:** High-performance pre-compiled regex matching filters out mismatched positions (e.g., mismatched experience requirements or outdated tech stacks) in milliseconds.
* **Scoring Tier:** Evaluates stack alignment, keywords, salary indicators, and target criteria to assign match scores to every vacancy.

### 3. Database Layer Optimizations
* Implements an asynchronous wrapper around SQLite via **aiosqlite**, featuring parameterized queries to prevent SQL injections.
* Custom database indices (`idx_jobs_score`, `idx_jobs_source_ext`) ensure high-speed querying of top-scoring leads as the database grows.

### 4. Advanced Telegram MVC Controls
* Developed using **aiogram v3** (Model-View-Controller framework).
* Integrates custom commands `/run` (force scraping cycles), `/top` (list recommendations), `/stats` (analytics), and `/cover` (auto-generate customized cover letter templates).

---

## 📂 Codebase Overview

```
job-hunter-bot-showcase/
├── main.py              # Orchestration entry point and APScheduler
├── config.py            # Strong-typed settings schema (dataclasses + python-dotenv)
├── database.py          # Asynchronous parameterized database wrapper (aiosqlite)
├── scorer.py            # Keyword heuristic and match scoring engines
├── bot.py               # MVC architecture Telegram Bot command handlers (aiogram v3)
├── Dockerfile           # Production Docker container definition
├── docker-compose.yml   # One-click Docker Compose deployment specification
├── .env.example         # Environment configuration template
├── requirements.txt     # Dependency locklist
└── parsers/             # Concurrent scraping microservices
    ├── base.py          # Abstract scraper class with retry logic & request sessions
    └── example_parser.py# Extensible BeautifulSoup HTML scraping subclass
```

---

## 🚀 Quick Start (Docker Containerized)

The easiest way to run the orchestrator in production or locally is via **Docker Compose**:

```bash
# 1. Clone the repository
git clone https://github.com/klmtzz/job-hunter-bot.git
cd job-hunter-bot

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your BOT_TOKEN and TELEGRAM_CHAT_ID

# 3. Launch via Docker Compose
docker-compose up -d --build
```

### 🛠️ Local Python Setup (Without Docker)

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment configuration
cp .env.example .env

# 4. Run the orchestrator
python main.py
```

---

## 📝 Design Patterns Demonstrated
* **Abstract Factory / Base Template:** Used in `BaseParser` to enforce schema constraints on scraper subclasses.
* **Singleton / Global Config:** Configurations are initialized once in `config.py` and exported cleanly.
* **Separation of Concerns (SoC):** Database manipulation, scoring algorithms, and messaging protocols are decoupled and isolated.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.
