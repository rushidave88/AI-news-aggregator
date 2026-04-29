
import feedparser
import http.cookiejar
from pathlib import Path
from datetime import datetime
from requests import Session
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from news_aggregator.config import settings
from news_aggregator.models import ArticleCreate


# ─── CHANNELS TO FOLLOW ──────────────────────────────────────────────
YOUTUBE_CHANNELS = [
    {"id": "UCupvZG-5ko_eiXAupbDfxWw", "name": "CNN"},
    {"id": "UCBi2mrWuNuyYy4gbM6fU18Q", "name": "ABC News"},
    {"id": "UCeY0bbntWzzVIaj2z3QigXg", "name": "NBC News"},
    {"id": "UCIvaYmPQoCDEMUBqKkCQZPQ", "name": "NDTV"},
]



def get_rss_url(channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def extract_video_id(video_url: str) -> str:
    """
    Handles all YouTube URL formats:
    Normal:  https://youtube.com/watch?v=dQw4w9WgXcQ  → dQw4w9WgXcQ
    Shorts:  https://youtube.com/shorts/dQw4w9WgXcQ   → dQw4w9WgXcQ
    Short:   https://youtu.be/dQw4w9WgXcQ             → dQw4w9WgXcQ
    """
    if "/shorts/" in video_url:
        return video_url.split("/shorts/")[-1].split("?")[0]
    if "youtu.be/" in video_url:
        return video_url.split("youtu.be/")[-1].split("?")[0]
    if "v=" in video_url:
        return video_url.split("v=")[-1].split("&")[0]
    return video_url



def build_session() -> Session:
    """
    Creates a requests Session with:
    - Browser-like User-Agent header
    - YouTube cookies (if cookies.txt exists)
    """
    session = Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    })

    cookies_path = Path(settings.youtube_cookies_path)
    if cookies_path.exists():
        cookie_jar = http.cookiejar.MozillaCookieJar()
        cookie_jar.load(
            str(cookies_path),
            ignore_discard=True,
            ignore_expires=True
        )
        session.cookies = cookie_jar  # type: ignore
        print(f"🍪 Cookies loaded from {cookies_path}")
    else:
        print(f"⚠️  No cookies.txt found at {cookies_path}")

    return session


# ─── FETCH VIDEOS FROM ONE CHANNEL 
def fetch_channel_videos(
    channel_id: str,
    channel_name: str,
    max_videos: int = 5
) -> list[dict]:
    """
    Reads YouTube RSS feed and returns latest N videos.
    Skips YouTube Shorts automatically.
    """
    rss_url = get_rss_url(channel_id)
    print(f"\n📡 Fetching: {channel_name}")

    try:
        feed = feedparser.parse(rss_url)

        if not feed.entries:
            print(f"⚠️  No videos found for {channel_name}")
            return []

        videos = []
        for entry in feed.entries:

            if len(videos) >= max_videos:
                break

            video_url = entry.link

            # Skip YouTube Shorts
            if "/shorts/" in video_url:
                print(f"⏭️  Skipping Short: {entry.title[:40]}")
                continue

            video_id = extract_video_id(video_url)
            published_at = datetime(*entry.published_parsed[:6])
            thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

            videos.append({
                "video_id":     video_id,
                "title":        entry.title,
                "channel_name": channel_name,
                "channel_id":   channel_id,
                "published_at": published_at,
                "video_url":    video_url,
                "thumbnail_url": thumbnail_url,
            })

        print(f"✅ Found {len(videos)} videos")
        return videos

    except Exception as e:
        print(f"❌ Error fetching {channel_name}: {e}")
        return []

# ─── GET TRANSCRIPT 
def get_transcript(video_id: str) -> str | None:
    """
    Extracts full spoken transcript from a YouTube video.
    Uses cookies to bypass YouTube IP blocks in Docker.
    Returns None if no transcript available.
    """
    # Safety check
    if "http" in video_id or "/" in video_id:
        print(f"⚠️  Invalid video ID (got URL): {video_id[:50]}")
        return None

    try:
        session = build_session()
        ytt_api = YouTubeTranscriptApi(http_client=session)
        transcript_data = ytt_api.fetch(video_id)

        full_transcript = " ".join(
            chunk.get("text", "") for chunk in transcript_data
        )
        full_transcript = full_transcript.replace("\n", " ").strip()

        print(f"📝 Transcript: {len(full_transcript)} characters")
        return full_transcript

    except TranscriptsDisabled:
        print(f"⚠️  Transcripts disabled: {video_id}")
        return None

    except NoTranscriptFound:
        print(f"⚠️  No English transcript: {video_id}")
        return None

    except Exception as e:
        print(f"❌ Transcript error {video_id}: {e}")
        return None



def scrape_all_channels() -> list[ArticleCreate]:
    """
    Master function called by scheduler.py every hour.
    """
    all_articles = []

    for channel in YOUTUBE_CHANNELS:

        videos = fetch_channel_videos(
            channel_id=channel["id"],
            channel_name=channel["name"],
            max_videos=5
        )

        for video in videos:

            transcript = get_transcript(video["video_id"])

            article = ArticleCreate(
                video_id=    video["video_id"],
                title=       video["title"],
                channel_name=video["channel_name"],
                channel_id=  video["channel_id"],
                published_at=video["published_at"],
                video_url=   video["video_url"],
                thumbnail_url=video["thumbnail_url"],
                transcript=  transcript,
                is_processed=False,
                is_emailed=  False,
            )

            all_articles.append(article)
            print(f"✅ Scraped: {video['title'][:55]}")

    print(f"\n📦 Total scraped: {len(all_articles)} articles")
    return all_articles