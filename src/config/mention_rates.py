"""
Per-subreddit Kaiwa mention probability rates.

Strategy:
- High-risk subs (strict mods, tech-savvy users): Pure value only
- Medium-risk subs: Light touch
- Lower-risk subs (smaller, tool-friendly): Can be bolder
"""

# Per-subreddit mention rates (0.0 = never, 1.0 = always)
SUBREDDIT_MENTION_RATES: dict[str, float] = {
    # ===========================================
    # HIGH RISK - Pure Value Only (0%)
    # Build credibility, never promote
    # ===========================================
    "languagelearning": 0.0,      # 1.5M+ members, strict mods, instant shill detection
    "LearnJapanese": 0.0,         # Notoriously strict, very tech-savvy community
    "Korean": 0.0,                # Similar strict culture
    "ChineseLanguage": 0.0,       # Active mods, skeptical of app recs
    "Chinese": 0.0,               # Same community
    "japanese": 0.0,              # Related to LearnJapanese

    # ===========================================
    # MEDIUM RISK - Light Touch (10-15%)
    # Decent-sized but slightly more forgiving
    # ===========================================
    "learnspanish": 0.15,         # Large but more casual
    "Spanish": 0.15,
    "French": 0.15,               # Active but less aggressive moderation
    "learnfrench": 0.15,
    "German": 0.12,
    "learngerman": 0.12,
    "Portuguese": 0.15,           # Mid-size, engaged
    "learnportuguese": 0.15,
    "Italian": 0.15,
    "italianlearning": 0.15,
    "polyglot": 0.12,             # Smaller, people share tools often
    "language_exchange": 0.10,    # Exchange-focused, be careful
    "EnglishLearning": 0.15,
    "ENGLISH": 0.15,
    "Russian": 0.18,              # Mid-size but tool-friendly
    "learnRussian": 0.18,

    # ===========================================
    # LOWER RISK - Can Be Bolder (25-35%)
    # Smaller communities, less scrutiny
    # ===========================================
    "learnVietnamese": 0.30,      # Small, appreciate any help
    "Vietnamese": 0.30,
    "Turkish": 0.28,              # Less saturated with tool spam
    "turkishlearning": 0.28,
    "Indonesian": 0.30,
    "learnIndonesian": 0.30,
    "Hindi": 0.30,                # Underserved, welcome recommendations
    "learnHindi": 0.30,
    "Filipino": 0.30,
    "Tagalog": 0.30,
    "LearnDutch": 0.25,           # Smaller community, friendlier
    "Dutch": 0.25,
    "MandarinChinese": 0.20,      # Smaller than main Chinese subs
    "hanguk": 0.22,               # Smaller Korean sub
}

# Default rate for subreddits not in the list
DEFAULT_MENTION_RATE = 0.20


def get_mention_rate(subreddit: str) -> float:
    """
    Get the Kaiwa mention probability for a specific subreddit.

    Args:
        subreddit: Subreddit name (case-insensitive lookup)

    Returns:
        Mention probability (0.0 to 1.0)
    """
    # Try exact match first, then case-insensitive
    if subreddit in SUBREDDIT_MENTION_RATES:
        return SUBREDDIT_MENTION_RATES[subreddit]

    # Case-insensitive fallback
    subreddit_lower = subreddit.lower()
    for sub, rate in SUBREDDIT_MENTION_RATES.items():
        if sub.lower() == subreddit_lower:
            return rate

    return DEFAULT_MENTION_RATE


def is_value_only_subreddit(subreddit: str) -> bool:
    """Check if a subreddit should only get pure-value comments (no mentions)."""
    return get_mention_rate(subreddit) == 0.0
