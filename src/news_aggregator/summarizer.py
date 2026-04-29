# src/news_aggregator/summarizer.py

import json
from groq import Groq
from pydantic import ValidationError

from news_aggregator.config import settings
from news_aggregator.models import ArticleSummary
from news_aggregator.database import (
    get_unprocessed_articles,
    update_article_summary
)


# ─── GROQ CLIENT ─────────────────────────────────────────────────────
client = Groq(api_key=settings.groq_api_key)
MODEL  = "llama-3.3-70b-versatile"
MAX_TRANSCRIPT_LENGTH = 8000


# ─── SYSTEM PROMPT ────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a professional news editor. Your job is to analyze YouTube 
news video transcripts and return structured JSON summaries.

Always respond with ONLY valid JSON in this exact format:
{
    "summary": "3-4 sentence factual summary of the news story",
    "category": "one of: politics, technology, business, sports, health, entertainment, world, science",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}

Rules:
- summary must be factual, 3-4 sentences, no opinions
- category must be exactly one of the 8 options listed
- tags must be 3-5 lowercase keywords relevant to the story
- Return ONLY the JSON object, nothing else
"""


# ─── SUMMARIZE WITH FULL TRANSCRIPT ──────────────────────────────────
def summarize_article(video_id: str, title: str, transcript: str) -> ArticleSummary | None:
    """
    Sends transcript to Groq LLM and returns a structured summary.
    Returns None if Groq fails or returns invalid response.
    """
    trimmed_transcript = transcript[:MAX_TRANSCRIPT_LENGTH]
    if len(transcript) > MAX_TRANSCRIPT_LENGTH:
        print(f"✂️  Transcript trimmed: {len(transcript)} → {MAX_TRANSCRIPT_LENGTH} chars")

    user_message = f"""
Video Title: {title}

Transcript:
{trimmed_transcript}

Please summarize this news video.
"""

    try:
        print(f"🤖 Calling Groq for: {title[:50]}")

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        raw_response = response.choices[0].message.content
        print(f"📨 Groq responded ({len(raw_response)} chars)")

        response_dict = json.loads(raw_response)
        article_summary = ArticleSummary(**response_dict)

        print(f"✅ Summary: {article_summary.summary[:80]}...")
        return article_summary

    except json.JSONDecodeError as e:
        print(f"❌ Groq returned invalid JSON for {video_id}: {e}")
        return None

    except ValidationError as e:
        print(f"❌ Groq response missing fields for {video_id}: {e}")
        return None

    except Exception as e:
        print(f"❌ Groq API error for {video_id}: {e}")
        return None


# ─── SUMMARIZE BY TITLE ONLY (FALLBACK) ──────────────────────────────
def summarize_by_title(title: str) -> ArticleSummary | None:
    """
    Fallback: generates summary using only the video title.
    Used when transcript is unavailable (IP block / captions disabled).
    """
    user_message = f"""
Based only on this news video title, generate a plausible structured summary.

Video Title: {title}

Since we only have the title, keep the summary brief and factual.
"""

    try:
        print(f"📰 Summarizing by title only: {title[:50]}")

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"},
        )

        raw_response = response.choices[0].message.content
        response_dict = json.loads(raw_response)
        article_summary = ArticleSummary(**response_dict)

        print(f"✅ Title-only summary done")
        return article_summary

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON from Groq (title-only): {e}")
        return None

    except ValidationError as e:
        print(f"❌ Missing fields from Groq (title-only): {e}")
        return None

    except Exception as e:
        print(f"❌ Groq API error (title-only): {e}")
        return None


# ─── PROCESS ALL UNPROCESSED ARTICLES ────────────────────────────────
def process_unprocessed_articles() -> None:
    """
    Master function called by scheduler.py every hour.
    1. Fetches all articles without a summary
    2. Calls Groq for each one (transcript or title-only)
    3. Saves the summary back to the database
    """
    articles = get_unprocessed_articles()

    if not articles:
        print("✅ No unprocessed articles found.")
        return

    print(f"\n🔄 Processing {len(articles)} articles with Groq...")

    success_count = 0
    fail_count    = 0

    for article in articles:

        # Use full transcript if available, else fall back to title only
        if article.transcript:
            result = summarize_article(
                video_id=article.video_id,
                title=article.title,
                transcript=article.transcript
            )
        else:
            result = summarize_by_title(article.title)

        if result:
            update_article_summary(
                video_id=article.video_id,
                summary=result.summary,
                category=result.category,
                tags=result.tags
            )
            success_count += 1
        else:
            print(f"⚠️  Failed to summarize: {article.title[:50]}")
            fail_count += 1

    print(f"\n📊 Done! Summarized: {success_count} | Failed: {fail_count}")