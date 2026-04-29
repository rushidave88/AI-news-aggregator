# main.py

from news_aggregator.scraper import scrape_all_channels
from news_aggregator.summarizer import process_unprocessed_articles
from news_aggregator.mailer import send_daily_digest
from news_aggregator.database import init_db

def main():
    print("🚀 AI News Aggregator starting...")

    # 1. Initialize database tables
    init_db()

    # 2. Scrape YouTube channels
    print("\n📡 STEP 1 — Scraping YouTube channels...")
    scrape_all_channels()

    # 3. Summarize with Groq
    print("\n🤖 STEP 2 — Summarizing with Groq...")
    process_unprocessed_articles()

    # 4. Send email digest
    print("\n📧 STEP 3 — Sending email digest...")
    send_daily_digest()

    print("\n✅ Pipeline complete!")

if __name__ == "__main__":
    main()