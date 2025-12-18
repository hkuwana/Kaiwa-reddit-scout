# Kaiwa Reddit Scout

A Python tool that finds language learners on Reddit who need help with speaking practice, scores them with AI, and generates personalized comment drafts.

## What It Does

1. **Scrapes** Reddit for posts about language learning struggles
2. **Filters** using 208 trigger keywords (speaking anxiety, practice gaps, etc.)
3. **Scores** each lead 1-10 using AI (Gemma - free)
4. **Evaluates** if the post is worth commenting on
5. **Generates** natural Reddit comments and DM drafts (Gemini - better quality)
6. **Saves** to CSV and Google Sheets

---

## Prerequisites

Before starting, you'll need accounts for:

| Service | What For | Sign Up |
|---------|----------|---------|
| Reddit | API access to read posts | [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) |
| Google AI Studio | Gemini/Gemma API for AI analysis | [aistudio.google.com](https://aistudio.google.com/apikey) |
| Google Cloud (optional) | Sheets export | [console.cloud.google.com](https://console.cloud.google.com/) |

**System requirements:**
- Python 3.10+
- pip (Python package manager)

---

## Setup (Step by Step)

### Step 1: Clone the Repository

```bash
git clone https://github.com/hkuwana/Kaiwa-reddit-scout.git
cd Kaiwa-reddit-scout
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Create Your `.env` File

```bash
cp .env.example .env
```

Now open `.env` in your editor and fill in each section:

---

### Step 4: Get Reddit API Credentials

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **"create another app..."** at the bottom
3. Fill in:
   - Name: `KaiwaScout` (or anything)
   - Type: Select **"script"**
   - Redirect URI: `http://localhost:8080`
4. Click **Create app**
5. Copy the credentials to your `.env`:

```bash
REDDIT_CLIENT_ID=abc123xyz        # Under "personal use script"
REDDIT_CLIENT_SECRET=secret123    # The "secret" field
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
```

---

### Step 5: Get Google AI (Gemini) API Key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **"Create API Key"**
3. Copy the key to your `.env`:

```bash
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemma-3-27b-it           # Free model for scoring
RESPONSE_MODEL=gemini-2.0-flash       # Better model for comments
```

**Available models:**
| Model | Cost | Best For |
|-------|------|----------|
| `gemma-3-27b-it` | Free | Scoring, filtering |
| `gemini-2.0-flash` | Cheap | Comment generation |
| `gemini-1.5-pro` | More expensive | Highest quality |

---

### Step 6: (Optional) Set Up Google Sheets

This lets you export leads to a Google Sheet automatically.

#### 6a. Create a Service Account

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable these APIs:
   - [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com)
   - [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)
4. Go to **IAM & Admin → Service Accounts**
5. Click **Create Service Account**
6. Name it `kaiwa-scout` and click **Create**
7. Skip the optional steps, click **Done**
8. Click on your new service account
9. Go to **Keys** tab → **Add Key** → **Create new key** → **JSON**
10. Download the JSON file

#### 6b. Add Credentials to `.env`

Open the downloaded JSON and copy its contents:

```bash
GOOGLE_CREDENTIALS_JSON={"type": "service_account", "project_id": "...", ...}
GOOGLE_SHEET_NAME=Kaiwa-Scout
```

#### 6c. (Optional) Domain-Wide Delegation

If you want sheets created in YOUR Drive (not the service account's):

1. In Cloud Console, click on your service account
2. Expand **Advanced settings** and copy the **Client ID**
3. Go to [admin.google.com](https://admin.google.com) → Security → API Controls → Domain-wide Delegation
4. Click **Add new**
5. Enter:
   - Client ID: (from step 2)
   - Scopes: `https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive`
6. Add to your `.env`:

```bash
GOOGLE_IMPERSONATE_EMAIL=your-email@yourdomain.com
```

---

## Test Your Setup

### Test All APIs

```bash
python3 test_apis.py
```

### Test Individual Components

```bash
# Test Reddit connection
python3 test_apis.py --reddit

# Test Gemini AI
python3 test_apis.py --gemini

# Test Google Sheets
python3 test_apis.py --sheets
```

### Run with Mock Data (No API needed)

```bash
python3 -m src.main --mock --analyze --limit 5 -v
```

---

## Usage

### Basic Commands

```bash
# Scrape and filter only (no AI)
python3 -m src.main --limit 50

# With AI analysis (scoring + comments)
python3 -m src.main --analyze --limit 50

# With Google Sheets export
python3 -m src.main --analyze --sheets --limit 50

# Verbose output
python3 -m src.main --analyze --limit 50 -v

# Specific subreddits only
python3 -m src.main --analyze -s languagelearning,LearnJapanese --limit 30
```

### CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--analyze` | `-a` | Enable AI scoring and comment generation |
| `--sheets` | | Export to Google Sheets |
| `--verbose` | `-v` | Show detailed output |
| `--limit N` | `-l N` | Max posts to fetch (default: 100) |
| `--subreddits X,Y` | `-s X,Y` | Specific subreddits |
| `--mock` | `-m` | Use mock data for testing |
| `--config` | `-c` | Show current configuration |

---

## Run Automatically (Background)

### Quick Start: Use the Runner Script

The easiest way to run the scout continuously:

```bash
# Run once (test your setup)
./run_scout.sh

# Run continuously every hour
./run_scout.sh loop

# Run in background (survives terminal close)
./run_scout.sh bg
```

**To stop the background process:**
```bash
pkill -f 'run_scout.sh loop'
```

**To check logs:**
```bash
tail -f logs/scout.log
```

### Alternative: Cron (Linux/Mac)

For more control over scheduling:

```bash
# Open crontab
crontab -e

# Add this line (runs every hour)
0 * * * * cd /path/to/Kaiwa-reddit-scout && ./run_scout.sh >> logs/scout.log 2>&1
```

**Common schedules:**
| Schedule | Cron Expression |
|----------|-----------------|
| Every hour | `0 * * * *` |
| Every 6 hours | `0 */6 * * *` |
| Every day at 9am | `0 9 * * *` |
| Every 30 minutes | `*/30 * * * *` |

---

## Configuration Options

All settings go in your `.env` file:

### AI Models

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_MODEL` | `gemma-3-27b-it` | Model for scoring (use free model) |
| `RESPONSE_MODEL` | `gemini-2.0-flash` | Model for comments (use better model) |
| `SIGNAL_THRESHOLD` | `7` | Minimum score to generate comments (1-10) |
| `REQUIRE_COMMENT_WORTHY` | `true` | Evaluate if post is worth commenting on |

### Google Sheets

| Variable | Description |
|----------|-------------|
| `GOOGLE_CREDENTIALS_JSON` | Service account JSON (inline) |
| `GOOGLE_SHEET_NAME` | Sheet name prefix (date auto-appended) |
| `GOOGLE_FOLDER_ID` | Optional: Create sheets in this folder |
| `GOOGLE_IMPERSONATE_EMAIL` | Optional: Use domain-wide delegation |

---

## How It Works

```
Reddit Posts
     ↓
[Keyword Filter] → 208 triggers, 68 exclusions
     ↓
[AI Scoring] → Gemma rates 1-10
     ↓
[Worth Commenting?] → Skip venting/generic posts
     ↓
[Generate Comments] → Gemini creates drafts
     ↓
CSV + Google Sheets
```

### Signal Scores

| Score | Type | Meaning |
|-------|------|---------|
| 8-10 | HIGH | Speaking anxiety, actively seeking help |
| 5-7 | MEDIUM | Related struggles, not main focus |
| 1-4 | LOW | Probably won't benefit |

### Categories

- **Speaking Anxiety** - Fear of speaking, freezing up
- **Practice Gap** - No conversation partners
- **Immersion Prep** - Moving abroad, meeting in-laws
- **Plateau Frustration** - Stuck, not progressing
- **App Fatigue** - Duolingo isn't working

---

## Output

### CSV File (`data/leads.csv`)

Contains all leads with:
- Post details (title, URL, author)
- Matched keywords
- AI score and category
- Comment-worthy evaluation
- Generated comment and DM drafts

### Google Sheets

Auto-dated sheets (e.g., `Kaiwa-Scout-2025-12-18`) with the same data, formatted for easy review.

---

## Troubleshooting

### "Drive storage quota exceeded"

The service account's Drive is full. Options:
1. Delete old sheets from the service account
2. Use `GOOGLE_IMPERSONATE_EMAIL` to use your Drive instead
3. Remove `GOOGLE_FOLDER_ID` to let it create sheets in its own space

### "Gemini API error"

1. Check your API key is correct
2. Verify the model name exists (try `gemini-1.5-flash` if unsure)
3. Check your quota at [aistudio.google.com](https://aistudio.google.com)

### "Reddit 403 Forbidden"

1. Verify your Reddit credentials
2. Make sure your app type is "script"
3. Check if your account has 2FA (may need app password)

---

## Costs

| Service | Free Tier | Notes |
|---------|-----------|-------|
| Reddit API | Unlimited | 60 requests/min limit |
| Gemma (scoring) | 1,500 req/day | Free via Google AI Studio |
| Gemini Flash | ~$0.01/1K tokens | Very cheap |
| Google Sheets | Unlimited | Free with service account |

**Estimated cost:** $2-5/month for 100 posts/day with AI analysis.

---

## License

MIT
