# src/news_aggregator/mailer.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from jinja2 import Template

from news_aggregator.config import settings
from news_aggregator.models import NewsArticle
from news_aggregator.database import (
    get_unemailed_articles,
    get_active_subscribers,
    mark_articles_as_emailed
)


# ─── HTML EMAIL TEMPLATE ─────────────────────────────────────────────
# Jinja2 template — {{ variable }} gets replaced with real values
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body        { font-family: Arial, sans-serif; background:#f4f4f4; margin:0; padding:0; }
    .container  { max-width:680px; margin:30px auto; background:#ffffff; border-radius:8px; overflow:hidden; }
    .header     { background:#1a1a2e; color:#ffffff; padding:30px; text-align:center; }
    .header h1  { margin:0; font-size:24px; letter-spacing:2px; }
    .header p   { margin:8px 0 0; color:#aaaaaa; font-size:13px; }
    .section    { padding:10px 30px 0; }
    .category   { font-size:11px; font-weight:bold; text-transform:uppercase;
                  color:#ffffff; background:#e63946; padding:3px 10px;
                  border-radius:4px; display:inline-block; margin-bottom:8px; }
    .article    { border-bottom:1px solid #eeeeee; padding:20px 0; }
    .article:last-child { border-bottom:none; }
    .article h2 { font-size:17px; margin:0 0 8px; color:#1a1a2e; line-height:1.4; }
    .article p  { font-size:14px; color:#555555; line-height:1.7; margin:0 0 10px; }
    .meta       { font-size:12px; color:#999999; margin-bottom:8px; }
    .tags       { margin-top:8px; }
    .tag        { display:inline-block; background:#f0f0f0; color:#666;
                  font-size:11px; padding:2px 8px; border-radius:12px; margin:2px; }
    .watch-btn  { display:inline-block; margin-top:10px; padding:8px 18px;
                  background:#1a1a2e; color:#ffffff; text-decoration:none;
                  border-radius:4px; font-size:13px; }
    .footer     { background:#f4f4f4; text-align:center; padding:20px;
                  font-size:12px; color:#aaaaaa; }
    .count-bar  { background:#1a1a2e; color:#ffffff; text-align:center;
                  padding:12px; font-size:13px; }
  </style>
</head>
<body>
  <div class="container">

    <!-- HEADER -->
    <div class="header">
      <h1>📰 AI News Digest</h1>
      <p>{{ date }} &nbsp;·&nbsp; {{ total }} stories from {{ channels }} channels</p>
    </div>

    <!-- ARTICLE COUNT BAR -->
    <div class="count-bar">
      Today's top stories, summarized by AI
    </div>

    <!-- ARTICLES GROUPED BY CATEGORY -->
    {% for category, articles in grouped.items() %}
    <div class="section">
      <br>
      <span class="category">{{ category }}</span>

      {% for article in articles %}
      <div class="article">
        <div class="meta">{{ article.channel_name }} &nbsp;·&nbsp; {{ article.published_at.strftime('%b %d, %Y %I:%M %p') }}</div>
        <h2>{{ article.title }}</h2>
        <p>{{ article.summary }}</p>
        <div class="tags">
          {% for tag in article.tags %}
          <span class="tag">#{{ tag }}</span>
          {% endfor %}
        </div>
        <a href="{{ article.video_url }}" class="watch-btn">▶ Watch Video</a>
      </div>
      {% endfor %}

    </div>
    {% endfor %}

    <!-- FOOTER -->
    <div class="footer">
      AI News Aggregator &nbsp;·&nbsp; Powered by Groq + Llama 3<br>
      Articles sourced from YouTube news channels
    </div>

  </div>
</body>
</html>
"""


# ─── GROUP ARTICLES BY CATEGORY ──────────────────────────────────────
def group_by_category(articles: list[NewsArticle]) -> dict[str, list[NewsArticle]]:
    """
    Groups articles by their category for organized email layout.

    Input:  [article1(politics), article2(tech), article3(politics)]
    Output: {"politics": [article1, article3], "technology": [article2]}
    """
    grouped = {}
    for article in articles:
        category = article.category or "general"
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(article)
    return grouped


# ─── BUILD HTML EMAIL ─────────────────────────────────────────────────
def build_email_html(articles: list[NewsArticle]) -> str:
    """
    Renders the Jinja2 HTML template with real article data.
    Returns the final HTML string ready to send.
    """
    grouped = group_by_category(articles)

    # Count unique channels in today's digest
    channels = len(set(a.channel_name for a in articles))

    # Render template — replaces {{ variables }} with real values
    template = Template(EMAIL_TEMPLATE)
    html = template.render(
        date=datetime.now().strftime("%A, %B %d %Y"),
        total=len(articles),
        channels=channels,
        grouped=grouped,
    )
    return html


# ─── SEND EMAIL ───────────────────────────────────────────────────────
def send_email(to_address: str, subject: str, html_body: str) -> bool:
    """
    Sends one HTML email via Gmail SMTP.
    Returns True if sent successfully, False if failed.
    """
    try:
        # Build the email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = settings.gmail_address
        msg["To"]      = to_address

        # Attach HTML body
        msg.attach(MIMEText(html_body, "html"))

        # Connect to Gmail SMTP and send
        # Port 465 = SSL (encrypted from the start)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(
                settings.gmail_address,
                settings.gmail_app_password
            )
            server.sendmail(
                settings.gmail_address,
                to_address,
                msg.as_string()
            )

        print(f"📧 Sent to: {to_address}")
        return True

    except Exception as e:
        print(f"❌ Failed to send to {to_address}: {e}")
        return False


# ─── MAIN FUNCTION ────────────────────────────────────────────────────
def send_daily_digest() -> None:
    """
    Master function called by scheduler.py every 24 hours.
    1. Gets all unsent summarized articles
    2. Builds HTML email
    3. Sends to all active subscribers
    4. Marks articles as emailed
    """
    print("\n📬 Starting daily digest...")

    # Step 1: Get articles ready to send
    articles = get_unemailed_articles()

    if not articles:
        print("📭 No new articles to send today.")
        return

    print(f"📰 Found {len(articles)} articles to include")

    # Step 2: Build the HTML email
    today = datetime.now().strftime("%A, %B %d %Y")
    subject = f"📰 AI News Digest — {today}"
    html_body = build_email_html(articles)

    # Step 3: Get all subscribers
    subscribers = get_active_subscribers()

    if not subscribers:
        print("⚠️  No active subscribers found.")
        return

    print(f"👥 Sending to {len(subscribers)} subscribers...")

    # Step 4: Send to each subscriber
    sent_count = 0
    for email in subscribers:
        success = send_email(
            to_address=email,
            subject=subject,
            html_body=html_body
        )
        if success:
            sent_count += 1

    # Step 5: Mark all articles as emailed
    # So they don't appear in tomorrow's digest
    article_ids = [a.id for a in articles]
    mark_articles_as_emailed(article_ids)

    print(f"\n✅ Digest sent to {sent_count}/{len(subscribers)} subscribers")
    print(f"📌 Marked {len(article_ids)} articles as emailed")