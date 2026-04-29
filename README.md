📰 AI News Aggregator
An automated news pipeline that scrapes YouTube news channels, summarizes videos using Groq LLM, stores them in PostgreSQL, and delivers a daily email digest — all running inside Docker.
 
🚀 Features
•	📡 YouTube Scraper — Fetches latest news videos from CNN, ABC News, and more
•	🤖 AI Summarizer — Uses Groq's llama-3.3-70b-versatile to generate structured summaries
•	🗄️ PostgreSQL Storage — Stores articles with metadata (category, tags, transcript)
•	📧 Daily Email Digest — Sends beautifully formatted HTML email with top stories
•	⏰ Auto Scheduler — Runs every hour automatically
•	🐳 Fully Dockerized — One command to run everything
 
🧱 Project Structure
ainewsaggregator/
├── src/
│   └── news_aggregator/
│       ├── config.py         # Settings and environment variables
│       ├── models.py         # Pydantic data models
│       ├── database.py       # PostgreSQL connection and queries
│       ├── scraper.py        # YouTube channel scraper
│       ├── summarizer.py     # Groq LLM summarization
│       ├── mailer.py         # Email digest sender
│       └── scheduler.py     # Hourly job runner
├── main.py                   # Entry point
├── Dockerfile                # App container definition
├── docker-compose.yml        # Multi-container orchestration
├── pyproject.toml            # Python dependencies (uv)
├── cookies.txt               # YouTube cookies (not committed)
├── .env                      # Secret keys (not committed)
└── .env.example              # Template for environment variables

 
⚙️ Tech Stack
Layer	Technology
Language	Python 3.12
Package Manager	uv
LLM	Groq API (llama-3.3-70b-versatile)
Database	PostgreSQL 15
YouTube Scraping	yt-dlp + youtube-transcript-api
Email	SMTP (Gmail App Password)
Containerization	Docker + Docker Compose
DB Browser	Adminer

 
🛠️ Local Setup
Prerequisites
•	Docker Desktop installed and running
•	A Groq API key (free)
•	A Gmail account with App Password enabled
1. Clone the Repository
git clone https://github.com/yourusername/ainewsaggregator.git
cd ainewsaggregator

2. Create Environment File
Copy the example and fill in your real values:
cp .env.example .env

Edit .env:
GROQ_API_KEY=your_groq_api_key_here
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_TO=recipient@gmail.com
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=news_db

3. Add YouTube Cookies (Optional but Recommended)
Export cookies from your browser using the EditThisCookie extension and save as cookies.txt in the root folder. This helps bypass YouTube transcript restrictions.
4. Run the App
docker compose up --build

The app will:
1.	Start PostgreSQL database
2.	Start the news aggregator app
3.	Begin scraping YouTube channels
4.	Summarize articles with Groq
5.	Send an email digest
 
🔑 Environment Variables
Variable	Description	Required
GROQ_API_KEY	Groq API key for LLM summarization	✅
EMAIL_USER	Gmail address to send from	✅
EMAIL_PASSWORD	Gmail App Password (not your login password)	✅
EMAIL_TO	Recipient email address	✅
POSTGRES_USER	PostgreSQL username	✅
POSTGRES_PASSWORD	PostgreSQL password	✅
POSTGRES_DB	PostgreSQL database name	✅

 
🗄️ Database Browser
Once the app is running, open Adminer in your browser:
http://localhost:8080

Field	Value
System	PostgreSQL
Server	db
Username	admin
Password	password
Database	news_db

 
📧 Email Digest
The app automatically sends a daily digest to your configured email. The email includes:
•	📌 Article title and source channel
•	📝 3–4 sentence AI-generated summary
•	🏷️ Category (politics, tech, sports, etc.)
•	🔖 Relevant tags
 
🐳 Docker Services
Service	Description	Port
news_app	Python news aggregator	—
news_db	PostgreSQL database	5432
adminer	Web-based DB browser	8080

Useful Docker Commands
# Start all services
docker compose up --build

# Start in background
docker compose up -d

# Stop all services
docker compose down

# View app logs
docker compose logs -f news_app

# Reset all articles (re-process)
docker compose exec db psql -U admin -d news_db -c \
  "UPDATE news_articles SET is_processed=FALSE, is_emailed=FALSE, summary=NULL, category=NULL, tags=NULL;"

# Manually trigger summarization
docker compose exec app uv run python -c \
  "from news_aggregator.summarizer import process_unprocessed_articles; process_unprocessed_articles()"

# Manually send email
docker compose exec app uv run python -c \
  "from news_aggregator.mailer import send_daily_digest; send_daily_digest()"

 
📡 News Sources
Currently scraping:
•	CNN — @CNN
•	ABC News — @ABCNews
To add more channels, edit the CHANNELS list in scraper.py:
CHANNELS = [
    {"name": "CNN",      "handle": "@CNN"},
    {"name": "ABC News", "handle": "@ABCNews"},
    {"name": "BBC News", "handle": "@BBCNews"},   # ← add more here
]

 
🤖 AI Summarization
Each article is summarized using Groq's llama-3.3-70b-versatile model. The output is structured JSON:
{
  "summary": "3-4 sentence factual summary of the news story",
  "category": "technology",
  "tags": ["ai", "regulation", "llm", "policy", "usa"]
}

Fallback behaviour: If YouTube blocks the transcript, the app falls back to summarizing using only the video title.
 
🔒 Security Notes
•	Never commit .env or cookies.txt to Git
•	Use Gmail App Passwords, not your actual Gmail password
•	Rotate your Groq API key if it gets exposed
 
☁️ Deployment
This project can be deployed to Render.com for free 24/7 operation:
•	Web Service — runs the Python app container
•	PostgreSQL — managed database (free 90-day tier)
•	Cron Job — replaces the local scheduler
Deployment guide coming soon.

 
🙏 Acknowledgements
•	Groq — blazing fast LLM inference
•	yt-dlp — YouTube metadata extraction
•	youtube-transcript-api — transcript fetching
•	Docker — containerization
