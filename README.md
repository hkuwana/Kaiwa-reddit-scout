# Kaiwa Reddit Scout

A modular Python pipeline to discover high-signal language learning leads on Reddit. Monitor subreddits for specific keywords, filter out noise, and surface actionable leads for manual outreach.

## Features

- **Multi-language support**: Japanese, Korean, Chinese, Spanish, French, German, and 10+ more languages
- **Smart filtering**: 208 trigger keywords catch high-signal posts; exclusion keywords filter out noise
- **AI-powered analysis**: Google Gemini/Gemma scores leads (1-10) and drafts personalized responses
- **Batch processing**: Efficient API usage with batch scoring to reduce costs
- **Flexible output**: Local CSV or auto-dated Google Sheets (e.g., `Kaiwa-Scout-2025-12-18`)
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
| Google AI | `GEMINI_API_KEY`, `GEMINI_MODEL`, `RESPONSE_MODEL` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| Google Sheets (optional) | `GOOGLE_CREDENTIALS_JSON`, `GOOGLE_SHEET_NAME`, `GOOGLE_FOLDER_ID` | [console.cloud.google.com](https://console.cloud.google.com/) |
| Resend (optional) | `RESEND_API_KEY`, `EMAIL_TO` | [resend.com/api-keys](https://resend.com/api-keys) |

**AI Model Configuration**:

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_MODEL` | `gemma-3-27b-it` | Model for scoring/filtering (use cheaper model) |
| `RESPONSE_MODEL` | `gemini-2.5-flash-lite` | Model for generating comments (use higher quality model) |
| `SIGNAL_THRESHOLD` | `7` | Minimum score for high-signal leads |
| `REQUIRE_COMMENT_WORTHY` | `true` | Evaluate if posts are worth commenting on before generating drafts |

**Recommended model configurations**:
- **Cost-optimized**: `GEMINI_MODEL=gemma-3-27b-it` + `RESPONSE_MODEL=gemini-2.5-flash-lite`
- **Quality-focused**: `GEMINI_MODEL=gemini-1.5-flash` + `RESPONSE_MODEL=gemini-1.5-pro`

### 3. Test your setup

```bash
# Test all APIs
python3 test_apis.py

# Test individual APIs
python3 test_apis.py --gemini
python3 test_apis.py --reddit
python3 test_apis.py --sheets
python3 test_apis.py --resend
```

### 4. Run the scout

```bash
# Basic run (scrape + filter only)
python3 -m src.main --limit 50

# With AI analysis (scoring + response drafts)
python3 -m src.main --analyze --limit 50

# Export to Google Sheets with timestamps
python3 -m src.main --analyze --sheets --limit 50

# Full verbose output
python3 -m src.main -a -v -l 50

# Specific subreddits only
python3 -m src.main -a -s languagelearning,LearnJapanese -l 30
```

## CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--analyze` | `-a` | Enable Gemini AI analysis (scoring + drafts) |
| `--sheets` | | Export to Google Sheets with timestamps |
| `--verbose` | `-v` | Show detailed output |
| `--limit N` | `-l N` | Max posts to fetch (default: 100) |
| `--subreddits X,Y` | `-s X,Y` | Specific subreddits (default: all 36) |
| `--mock` | `-m` | Use mock data (for testing) |
| `--config` | `-c` | Show configuration status |
| `--languages` | | List supported languages |

## How It Works

```
Reddit API  →  Keyword Filter  →  Google AI   →  CSV Output
   (PRAW)       (208 triggers)   (Gemini/Gemma)  (leads.csv)
                                   (Scoring)         ↓
                                   (Drafts)    Google Sheets
                                             (auto-dated daily)
```

### Pipeline Steps

1. **Fetch**: Get new posts from 36 language learning subreddits
2. **Filter**: Match against 208 trigger keywords, exclude 68 low-signal patterns
3. **Score**: AI rates each lead 1-10 with HIGH/MEDIUM/LOW classification (using `GEMINI_MODEL`)
4. **Evaluate**: Check if high-signal leads are worth commenting on (skip generic/venting posts)
5. **Draft**: Generate public comment and DM drafts only for worthy leads (using `RESPONSE_MODEL`)
6. **Save**: Output to `data/leads.csv` with all details
7. **Export** (optional): Create dated Google Sheet (e.g., `Kaiwa-Scout-2025-12-18`)

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
| `comment_worthy` | Whether this post is worth commenting on (yes/no) |
| `comment_worthy_reason` | Reason for the worthiness decision |
| `public_draft` | Suggested public comment (only for worthy leads) |
| `dm_draft` | Suggested DM message (only for worthy leads) |

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
| Google AI | gemma-3-27b-it | Free tier available | 1,500 req/day free |
| Google Sheets | - | Free | Requires service account |
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
│   ├── output/
│   │   └── sheets_client.py # Google Sheets export
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
| 3 | Google Sheets export with timestamps | ✅ Complete |
| 4 | Email notifications (Resend) | ✅ Ready |
| 5 | Scheduled automation | 📝 Manual (cron) |

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
