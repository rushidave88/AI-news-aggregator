# main.py

import sys
from pathlib import Path

# ─── ADD src/ TO PYTHON PATH ─────────────────────────────────────────
# Ensures Python can find news_aggregator package
sys.path.insert(0, str(Path(__file__).parent / "src"))

from news_aggregator.config import settings
from news_aggregator.database import create_tables, add_subscriber
from news_aggregator.scheduler import start_scheduler


def main():
    print("=" * 50)
    print("   📰 AI NEWS AGGREGATOR")
    print("=" * 50)

    # Step 1: Verify config loaded correctly
    print(f"\n✅ Config loaded")
    print(f"   Gmail:        {settings.gmail_address}")
    print(f"   DB:           {settings.database_url}")
    print(f"   Digest at:    {settings.digest_hour:02d}:00 AM")
    print(f"   Fetch every:  {settings.fetch_interval_minutes} mins")

    # Step 2: Create database tables (safe to run every time)
    print(f"\n🗄️  Setting up database...")
    create_tables()

    # Step 3: Add default subscriber from .env
    print(f"\n👤 Adding default subscriber...")
    add_subscriber(settings.digest_recipient)

    # Step 4: Start the scheduler (runs forever)
    print(f"\n⏰ Starting scheduler...")
    start_scheduler()


if __name__ == "__main__":
    main()