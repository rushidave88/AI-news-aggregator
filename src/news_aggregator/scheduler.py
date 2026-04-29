# src/news_aggregator/scheduler.py

import schedule
import time
from datetime import datetime

from news_aggregator.config import settings
from news_aggregator.scraper import scrape_all_channels
from news_aggregator.summarizer import process_unprocessed_articles
from news_aggregator.mailer import send_daily_digest
from news_aggregator.database import save_article


# ─── JOB 1: FETCH + SUMMARIZE ────────────────────────────────────────
def fetch_and_summarize() -> None:
    """
    Runs every hour:
    1. Scrapes latest videos from all YouTube channels
    2. Saves new ones to the database
    3. Summarizes unseen ones using Groq LLM
    """
    print(f"\n{'='*50}")
    print(f"⏰ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Hourly job started")
    print(f"{'='*50}")

    # Step 1: Scrape all channels
    print("\n📡 STEP 1 — Scraping YouTube channels...")
    articles = scrape_all_channels()

    # Step 2: Save each article to the database
    print(f"\n💾 STEP 2 — Saving {len(articles)} articles to database...")
    saved = 0
    for article in articles:
        result = save_article(article)
        if result:
            saved += 1
    print(f"✅ Saved {saved} new articles (duplicates skipped)")

    # Step 3: Summarize unprocessed articles
    print("\n🤖 STEP 3 — Summarizing with Groq LLM...")
    process_unprocessed_articles()

    print(f"\n✅ Hourly job complete!")


# ─── JOB 2: SEND EMAIL DIGEST ─────────────────────────────────────────
def send_digest() -> None:
    """
    Runs once every day at the configured hour (default 8AM):
    Sends the HTML email digest to all subscribers.
    """
    print(f"\n{'='*50}")
    print(f"📬 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Daily digest job started")
    print(f"{'='*50}")

    send_daily_digest()

    print(f"\n✅ Daily digest job complete!")


# ─── START SCHEDULER ──────────────────────────────────────────────────
def start_scheduler() -> None:
    """
    Sets up all scheduled jobs and starts the infinite loop.
    Called once from main.py when the app starts.
    """

    # ── Job 1: Fetch + Summarize every N minutes ──────────────────────
    interval = settings.fetch_interval_minutes
    schedule.every(interval).minutes.do(fetch_and_summarize)
    print(f"📅 Scheduled: fetch + summarize every {interval} minutes")

    # ── Job 2: Email digest once per day at configured hour ───────────
    digest_time = f"{settings.digest_hour:02d}:00"
    schedule.every().day.at(digest_time).do(send_digest)
    print(f"📅 Scheduled: email digest daily at {digest_time}")

    # ── Run both jobs ONCE immediately on startup ─────────────────────
    # So you don't have to wait 1 hour to see if everything works
    print("\n🚀 Running initial fetch immediately on startup...")
    fetch_and_summarize()

    print(f"\n⏳ Scheduler running... (Ctrl+C to stop)")
    print(f"   Next fetch in {interval} minutes")
    print(f"   Daily digest at {digest_time}\n")

    # ── Infinite loop — keeps checking for scheduled jobs ─────────────
    while True:
        schedule.run_pending()  # Run any job whose time has come
        time.sleep(60)          # Wait 60 seconds before checking again