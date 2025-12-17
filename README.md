# Kaiwa Reddit Scout

A modular Python pipeline to discover high-signal language learning leads on Reddit. Monitor subreddits for specific keywords, filter out noise, and surface actionable leads for manual outreach.

## Features

- **Multi-language support**: Japanese, Korean, Chinese, Spanish, French, German, and 10 more languages
- **Smart filtering**: Trigger keywords catch high-signal posts; exclusion keywords filter out noise
- **AI-powered analysis**: OpenAI scores leads and drafts personalized responses
- **Flexible output**: Local CSV, Google Sheets, or email notifications
- **Scheduled runs**: Run every 6 hours automatically

## Quick Start

### 1. Clone and setup

```bash
git clone https://github.com/yourusername/Kaiwa-reddit-scout.git
cd Kaiwa-reddit-scout

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure environment

```bash
# Copy example env file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

**Required for Phase 1 (MVP)**:
- `REDDIT_CLIENT_ID` - From [Reddit Apps](https://www.reddit.com/prefs/apps)
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USERNAME`
- `REDDIT_PASSWORD`

### 3. Run the scout

```bash
# Phase 1: Scrape and filter (outputs to CSV)
python -m src.main

# With options
python -m src.main --subreddits languagelearning,LearnJapanese --limit 50
```

## Architecture

```
Reddit API  →  Keyword Filter  →  AI Analysis  →  Output
   (PRAW)       (Python)         (OpenAI)      (CSV/Sheets)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed documentation.

## Project Structure

```
kaiwa-reddit-scout/
├── src/
│   ├── main.py              # Entry point
│   ├── config/              # Settings, languages, keywords
│   ├── scraper/             # Reddit API client, filters
│   ├── analyzer/            # OpenAI integration
│   ├── storage/             # CSV storage, data models
│   └── output/              # Google Sheets, email
├── data/                    # Output files (gitignored)
├── docs/                    # Documentation
├── .env.example             # Environment template
└── requirements.txt
```

## Phases

| Phase | Features | Status |
|-------|----------|--------|
| 1 | Reddit scraping + keyword filtering + CSV output | Planned |
| 2 | OpenAI analysis + response drafts | Planned |
| 3 | Google Sheets + email notifications | Planned |
| 4 | Scheduled automation (every 6 hours) | Planned |

## Supported Languages

Japanese, English, Spanish, French, German, Italian, Portuguese, Korean, Chinese, Hindi, Russian, Vietnamese, Dutch, Filipino, Indonesian, Turkish

## Configuration

### Trigger Keywords (High-Signal)
Posts containing these indicate strong leads:
- Emotional: "afraid to speak", "frustrated", "overwhelmed"
- Life events: "moving to", "in-laws", "job interview"
- App frustration: "duolingo isn't working", "can't speak"

### Exclusion Keywords (Low-Signal)
Posts containing these are filtered out:
- Tests: "JLPT", "HSK", "TOPIK", "N1-N5"
- Academic: "homework", "exam", "textbook"
- Media: "anime", "manga", "kdrama"

## Output

### CSV Format (Phase 1)
```
timestamp,subreddit,author,title,url,matched_keywords,language
```

### Google Sheets (Phase 3)
| Date | Link | Author | Language | Signal | Public Draft | DM Draft | Status |
|------|------|--------|----------|--------|--------------|----------|--------|

## Usage Notes

- **Manual outreach only**: Reddit ToS prohibits automated DMs
- **Respect rate limits**: 60 requests/minute for Reddit API
- **API costs**: ~$5/month for OpenAI at 100 posts/day

## Development

```bash
# Run tests
pytest

# Lint
ruff check src/

# Format
ruff format src/
```

## License

MIT
