# Kaiwa Reddit Scout - Architecture

## Overview

A modular pipeline to discover high-signal language learning leads on Reddit. The system monitors subreddits for specific keywords, filters out noise, and surfaces actionable leads for manual outreach.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Reddit    │───▶│   Filter    │───▶│  AI Brain   │───▶│   Output    │
│   (PRAW)    │    │  (Python)   │    │  (Gemini)   │    │(Sheets/CSV) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     Phase 1           Phase 1           Phase 2           Phase 3
```

---

## Phased Implementation

### Phase 1: Reddit Scraper (MVP)
**Goal**: Fetch and filter Reddit posts locally

**Components**:
- `src/scraper/reddit_client.py` - PRAW wrapper for Reddit API
- `src/scraper/keyword_filter.py` - Trigger/exclude keyword logic
- `src/storage/csv_storage.py` - Save leads to local CSV
- `src/config/languages.py` - Language definitions and keywords

**Output**: `data/leads.csv` with columns:
| timestamp | subreddit | author | title | url | matched_keywords |

**Run**: `python -m src.main --phase 1`

---

### Phase 2: AI Analysis ✅
**Goal**: Score leads and generate response drafts

**Components**:
- `src/analyzer/gemini_client.py` - Google Gemini API wrapper
- `src/analyzer/signal_scorer.py` - Determine HIGH/MEDIUM/LOW signal (1-10 score)
- `src/analyzer/response_generator.py` - Draft public comments & DMs

**Output**: Enhanced CSV with additional columns:
| ... | signal_score | signal_type | category | public_draft | dm_draft |

**Run**: `python -m src.main --analyze` (or `-a` flag)

---

### Phase 3: Dashboard & Notifications
**Goal**: Push to Google Sheets, send email digests

**Components**:
- `src/output/sheets_client.py` - Google Sheets API wrapper
- `src/output/email_notifier.py` - Email digest sender
- `src/output/formatter.py` - Format data for output

**Output**:
- Google Sheet with all leads
- Daily email digest of new HIGH signal leads

**Run**: `python -m src.main --phase 3`

---

### Phase 4: Automation
**Goal**: Run every 6 hours automatically

**Options**:
1. **Local**: Cron job or Python scheduler (APScheduler)
2. **Cloud**: Fly.io, Railway, or GitHub Actions

**Run**: `python -m src.scheduler`

---

## Directory Structure

```
kaiwa-reddit-scout/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── scheduler.py            # Scheduling logic
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Load .env, app config
│   │   ├── languages.py        # Language definitions
│   │   └── keywords.py         # Trigger/exclude keywords
│   │
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── reddit_client.py    # PRAW wrapper
│   │   └── keyword_filter.py   # Filter logic
│   │
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── gemini_client.py    # Google Gemini wrapper
│   │   ├── signal_scorer.py    # HIGH/MEDIUM/LOW classification
│   │   └── response_generator.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── csv_storage.py      # Local CSV
│   │   └── models.py           # Data models (dataclasses)
│   │
│   └── output/
│       ├── __init__.py
│       ├── sheets_client.py    # Google Sheets
│       ├── email_notifier.py   # Email alerts
│       └── formatter.py        # Output formatting
│
├── data/
│   ├── .gitkeep
│   └── leads.csv               # Generated leads (gitignored)
│
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py
│   ├── test_filter.py
│   └── test_analyzer.py
│
├── docs/
│   └── ARCHITECTURE.md         # This file
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── pyproject.toml
```

---

## Data Flow

### 1. Input: Reddit Posts
```python
{
    "id": "abc123",
    "subreddit": "languagelearning",
    "author": "user123",
    "title": "Struggling to speak Japanese with in-laws",
    "selftext": "I've been learning for 2 years but freeze up...",
    "url": "https://reddit.com/r/languagelearning/...",
    "created_utc": 1702800000
}
```

### 2. After Keyword Filter
```python
{
    ...
    "matched_triggers": ["in-laws", "freeze up", "Japanese"],
    "excluded": False,
    "language_detected": "Japanese"
}
```

### 3. After AI Analysis
```python
{
    ...
    "signal_score": 9,
    "signal_type": "HIGH",
    "category": "Speaking Anxiety - Family",
    "public_draft": "That in-laws situation sounds really tough...",
    "dm_draft": "Hey, saw your post about speaking with in-laws..."
}
```

### 4. Final Output (Google Sheets Row)
| Date | Link | Author | Language | Category | Signal | Public Draft | DM Draft | Status |
|------|------|--------|----------|----------|--------|--------------|----------|--------|
| 12/17 | [Link] | user123 | Japanese | Family | HIGH | "That in-laws..." | "Hey, saw..." | New |

---

## Supported Languages

| Language | Code | Subreddits to Monitor |
|----------|------|----------------------|
| Japanese | ja | r/LearnJapanese, r/Japanese |
| Korean | ko | r/Korean, r/hanguk |
| Chinese | zh | r/ChineseLanguage, r/Chinese |
| Spanish | es | r/learnspanish, r/Spanish |
| French | fr | r/French, r/learnfrench |
| German | de | r/German, r/learnGerman |
| Italian | it | r/italianlearning |
| Portuguese | pt | r/Portuguese, r/learnportuguese |
| Russian | ru | r/Russian, r/learnRussian |
| Hindi | hi | r/Hindi, r/learnHindi |
| Vietnamese | vi | r/Vietnamese, r/learnVietnamese |
| Dutch | nl | r/LearnDutch |
| Filipino | fil | r/Tagalog |
| Indonesian | id | r/Indonesian |
| Turkish | tr | r/turkishlearning |

**General**: r/languagelearning, r/language_exchange

---

## Keyword Strategy

### High-Signal Triggers (Examples)
```python
TRIGGER_KEYWORDS = [
    # Emotional/Deadline Pressure
    "afraid to speak", "scared to talk", "freeze up", "nervous",
    "frustrated", "overwhelmed", "giving up", "losing motivation",

    # Life Events
    "moving to", "relocating", "in-laws", "partner's family",
    "job interview", "work trip", "business meeting",

    # App Frustration
    "duolingo isn't working", "apps don't help", "still can't speak",
    "years of studying", "can read but can't speak",

    # Specific Needs
    "conversation practice", "speaking partner", "native speaker",
    "real conversations", "practical", "survival"
]
```

### Low-Signal Exclusions
```python
EXCLUDE_KEYWORDS = [
    # Test-focused (not conversation-focused)
    "JLPT", "HSK", "TOPIK", "DELE", "N1", "N2", "N3", "N4", "N5",

    # Academic
    "homework", "assignment", "exam", "test prep", "textbook",

    # Translation requests
    "translate this", "what does this mean", "help me translate",

    # Media consumption (passive, not active speaking)
    "anime", "manga", "drama", "kdrama", "subtitles",

    # Off-topic
    "tattoo", "song lyrics"
]
```

---

## API Rate Limits & Costs

### Reddit API (PRAW)
- **Rate**: 60 requests/minute (OAuth)
- **Cost**: Free
- **Strategy**: Use `stream.submissions()` for efficiency

### Google Gemini API
- **Model**: gemini-1.5-flash (default)
- **Cost**: ~$0.075 per 1M input tokens, ~$0.30 per 1M output tokens (50% cheaper than GPT-4o-mini)
- **Strategy**: Only analyze posts that pass keyword filter, generate responses only for high-signal leads
- **Budget**: ~$2-3/month for 100 posts/day
- **Free tier**: 1,500 requests/day for development

### Google Sheets API
- **Rate**: 300 requests/minute
- **Cost**: Free
- **Strategy**: Batch writes when possible

---

## Security Considerations

1. **Never commit `.env`** - Contains API keys
2. **Never commit `google_creds.json`** - Service account credentials
3. **Reddit ToS**: No automated DMs; manual action only
4. **Rate limiting**: Respect API limits to avoid bans
5. **Data privacy**: Don't store unnecessary user data

---

## Future Enhancements

- [ ] Web dashboard (Flask/FastAPI)
- [ ] Discord/Slack notifications
- [ ] Sentiment analysis improvements
- [ ] Multi-account Reddit monitoring
- [ ] Lead scoring ML model
- [ ] Response template A/B testing
