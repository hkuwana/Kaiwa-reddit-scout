# Kaiwa Reddit Scout

A modular Python pipeline to discover high-signal language learning leads on Reddit. Monitor subreddits for specific keywords, filter out noise, and surface actionable leads for manual outreach.

## Features

- **Multi-language support**: Japanese, Korean, Chinese, Spanish, French, German, and 10+ more languages
- **Smart filtering**: 208 trigger keywords catch high-signal posts; exclusion keywords filter out noise
- **AI-powered analysis**: Google Gemini scores leads (1-10) and drafts personalized responses
- **Batch processing**: Efficient API usage with batch scoring to reduce costs
- **Flexible output**: Local CSV with full lead details
- **Local execution**: Run manually or schedule with cron

## Quick Start

### 1. Clone and setup

```bash
git clone https://github.com/hkuwana/Kaiwa-reddit-scout.git
cd Kaiwa-reddit-scout

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip3 install -r requirements.txt
```

### 2. Configure environment

```bash
# Copy example env file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

**Required credentials**:

| Service | Variables | Get it at |
|---------|-----------|-----------|
| Reddit API | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`, `REDDIT_PASSWORD` | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) |
| Gemini API | `GEMINI_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Resend (optional) | `RESEND_API_KEY`, `EMAIL_TO` | [resend.com/api-keys](https://resend.com/api-keys) |

### 3. Test your setup

```bash
# Test all APIs
python3 test_apis.py

# Test individual APIs
python3 test_apis.py --gemini
python3 test_apis.py --reddit
python3 test_apis.py --resend
```

### 4. Run the scout

```bash
# Basic run (scrape + filter only)
python3 -m src.main --limit 50

# With AI analysis (scoring + response drafts)
python3 -m src.main --analyze --limit 50

# Full verbose output
python3 -m src.main -a -v -l 50

# Specific subreddits only
python3 -m src.main -a -s languagelearning,LearnJapanese -l 30
```

## CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--analyze` | `-a` | Enable Gemini AI analysis (scoring + drafts) |
| `--verbose` | `-v` | Show detailed output |
| `--limit N` | `-l N` | Max posts to fetch (default: 100) |
| `--subreddits X,Y` | `-s X,Y` | Specific subreddits (default: all 36) |
| `--mock` | `-m` | Use mock data (for testing) |
| `--config` | `-c` | Show configuration status |
| `--languages` | | List supported languages |

## How It Works

```
Reddit API  →  Keyword Filter  →  Gemini AI  →  CSV Output
   (PRAW)       (208 triggers)    (Scoring)    (leads.csv)
                                  (Drafts)
```

### Pipeline Steps

1. **Fetch**: Get new posts from 36 language learning subreddits
2. **Filter**: Match against 208 trigger keywords, exclude 68 low-signal patterns
3. **Score**: Gemini AI rates each lead 1-10 with HIGH/MEDIUM/LOW classification
4. **Draft**: Generate public comment and DM drafts for high-signal leads (score ≥7)
5. **Save**: Output to `data/leads.csv` with all details

### Signal Classification

| Score | Type | Description |
|-------|------|-------------|
| 8-10 | HIGH | Speaking anxiety, actively seeking solutions |
| 5-7 | MEDIUM | Related challenges, not primary focus |
| 1-4 | LOW | Unlikely to benefit from speaking practice |

### Categories

- **Speaking Anxiety** - Fear of speaking, nervousness
- **Practice Gap** - Lacks conversation partners
- **Immersion Prep** - Moving abroad, meeting in-laws
- **Plateau Frustration** - Stuck at a level
- **App Fatigue** - Frustrated with Duolingo etc.
- **General Learning** - General discussion

## Output Format

### CSV Columns

| Column | Description |
|--------|-------------|
| `scraped_at` | When the post was found |
| `subreddit` | Source subreddit |
| `author` | Reddit username |
| `title` | Post title |
| `post_url` | Direct link to post |
| `message_url` | Link to DM the user |
| `matched_triggers` | Keywords that matched |
| `language` | Detected target language |
| `signal_score` | AI score (1-10) |
| `signal_type` | HIGH/MEDIUM/LOW |
| `category` | Problem category |
| `public_draft` | Suggested public comment |
| `dm_draft` | Suggested DM message |

## Supported Languages

Japanese, Spanish, French, German, Italian, Portuguese, Korean, Chinese, Mandarin, Hindi, Russian, Vietnamese, Dutch, Filipino, Tagalog, Indonesian, Turkish

**Monitored subreddits**: 36 language learning communities including r/languagelearning, r/LearnJapanese, r/learnspanish, r/French, r/German, r/Korean, and more.

## Keyword Strategy

### Trigger Keywords (208 total)

**Language-specific patterns**:
- `speak [language]` - "speak japanese", "speak spanish"
- `learning [language]` - "learning korean", "learning french"
- `practice speaking [language]`
- `conversational [language]`
- `fluency in [language]`

**Emotional triggers**:
- "afraid to speak", "scared to talk", "freeze up"
- "frustrated", "overwhelmed", "giving up"

**Life events**:
- "moving to", "in-laws", "job interview"
- "deadline", "before i move"

**App frustration**:
- "duolingo isn't working", "quit duolingo"
- "still can't speak", "years of studying"

### Exclusion Keywords (68 total)

- Tests: JLPT, HSK, TOPIK, N1-N5
- Academic: homework, exam, textbook
- Media: anime, manga, kdrama
- Translation requests

## Scheduling (Local)

### Using cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Run every 6 hours
0 */6 * * * cd /path/to/Kaiwa-reddit-scout && /path/to/venv/bin/python -m src.main -a -l 100 >> logs/scout.log 2>&1
```

### Using launchd (Mac)

Create `~/Library/LaunchAgents/com.kaiwa.scout.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kaiwa.scout</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>-m</string>
        <string>src.main</string>
        <string>-a</string>
        <string>-l</string>
        <string>100</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/Kaiwa-reddit-scout</string>
    <key>StartInterval</key>
    <integer>21600</integer>
</dict>
</plist>
```

Load with: `launchctl load ~/Library/LaunchAgents/com.kaiwa.scout.plist`

## API Costs

| Service | Model | Cost | Notes |
|---------|-------|------|-------|
| Reddit | - | Free | 60 req/min rate limit |
| Gemini | gemini-1.5-flash | ~$0.075/1M input tokens | Free tier: 1,500 req/day |
| Resend | - | Free tier: 100 emails/day | Optional |

**Estimated monthly cost**: $2-5 for 100 posts/day with AI analysis.

## Project Structure

```
kaiwa-reddit-scout/
├── src/
│   ├── main.py              # Entry point
│   ├── config/
│   │   ├── settings.py      # Environment config
│   │   ├── languages.py     # Language definitions
│   │   └── keywords.py      # Trigger/exclusion keywords
│   ├── scraper/
│   │   ├── reddit_client.py # PRAW wrapper
│   │   └── keyword_filter.py# Filter logic
│   ├── analyzer/
│   │   ├── gemini_client.py # Gemini REST API
│   │   ├── signal_scorer.py # Lead scoring
│   │   └── response_generator.py # Draft generation
│   └── storage/
│       ├── csv_storage.py   # CSV output
│       └── models.py        # Data models
├── data/                    # Output files (gitignored)
├── test_apis.py             # API test script
├── .env.example             # Environment template
└── requirements.txt
```

## Implementation Status

| Phase | Features | Status |
|-------|----------|--------|
| 1 | Reddit scraping + keyword filtering + CSV output | ✅ Complete |
| 2 | Gemini AI analysis + signal scoring + response drafts | ✅ Complete |
| 3 | Google Sheets + email notifications | 🔄 Planned |
| 4 | Scheduled automation | 📝 Manual (cron) |

## Usage Notes

- **Manual outreach only**: Reddit ToS prohibits automated DMs. The tool generates drafts for you to review and send manually.
- **Respect rate limits**: PRAW handles Reddit's 60 req/min limit automatically.
- **Review before sending**: Always review AI-generated drafts before posting.

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
