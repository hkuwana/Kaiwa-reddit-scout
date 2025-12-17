"""
Keyword definitions for filtering Reddit posts.

HIGH-SIGNAL triggers: Indicate someone who needs conversation practice
LOW-SIGNAL exclusions: Filter out test-focused, academic, or off-topic posts
"""

# Supported languages for keyword generation
SUPPORTED_LANGUAGES = [
    "japanese", "spanish", "french", "german", "italian", "portuguese",
    "korean", "chinese", "mandarin", "hindi", "russian", "vietnamese",
    "dutch", "filipino", "tagalog", "indonesian", "turkish",
]

# High-signal trigger keywords
# Posts containing these indicate potential leads for conversation practice
TRIGGER_KEYWORDS: list[str] = [
    # === Language-specific keywords (generated) ===
    # "speak X" pattern
    *[f"speak {lang}" for lang in SUPPORTED_LANGUAGES],
    # "learning X" pattern
    *[f"learning {lang}" for lang in SUPPORTED_LANGUAGES],
    # "best way to learn X" pattern
    *[f"best way to learn {lang}" for lang in SUPPORTED_LANGUAGES],
    # "fluency in X" pattern
    *[f"fluency in {lang}" for lang in SUPPORTED_LANGUAGES],
    # "practice speaking X" pattern
    *[f"practice speaking {lang}" for lang in SUPPORTED_LANGUAGES],
    # "become conversational in X" pattern
    *[f"become conversational in {lang}" for lang in SUPPORTED_LANGUAGES],
    # "conversational X" pattern
    *[f"conversational {lang}" for lang in SUPPORTED_LANGUAGES],

    # === Speaking anxiety / emotional ===
    "afraid to speak",
    "scared to speak",
    "scared to talk",
    "nervous to speak",
    "anxiety when speaking",
    "speaking anxiety",
    "freeze up",
    "freeze up speaking",
    "freezing up",
    "blank out",
    "mind goes blank",
    "too shy",
    "embarrassed to speak",
    "frustrated",
    "overwhelmed",
    "losing motivation",
    "want to give up",
    "giving up",
    "stuck at",
    "hit a wall",
    "plateau",

    # === Life events / deadlines ===
    "moving to",
    "relocating to",
    "going to move",
    "in-laws",
    "in laws",
    "partner's family",
    "partners family",
    "spouse's family",
    "boyfriend's family",
    "girlfriend's family",
    "meeting family",
    "job interview",
    "work trip",
    "business meeting",
    "business trip",
    "need to learn fast",
    "need to learn quickly",
    "deadline",
    "before i move",
    "before moving",

    # === App/method frustration ===
    "duolingo isn't working",
    "duolingo doesn't work",
    "duolingo not helping",
    "quit duolingo",
    "beyond duolingo",
    "apps don't help",
    "apps aren't helping",
    "textbook isn't helping",
    "still can't speak",
    "can't speak",
    "can read but can't speak",
    "understand but can't speak",
    "years of studying",
    "studied for years",
    "been learning for",
    "learning for months",
    "learning for years",

    # === Heritage speakers / family ===
    "heritage speaker",
    "lost my language",
    "can't speak to relatives",
    "in-laws don't speak",
    "bilingual couple",
    "language barrier relationship",
    "conversational fluency",

    # === Specific needs ===
    "conversation practice",
    "speaking practice",
    "speaking partner",
    "conversation partner",
    "language partner",
    "native speaker",
    "real conversations",
    "actual conversations",
    "practical speaking",
    "everyday conversation",
    "daily conversation",
    "survival phrases",
    "need to speak",
    "want to speak",
    "improve my speaking",
    "practice speaking",

    # === Intermediate+ learners (higher intent) ===
    "intermediate",
    "upper intermediate",
    "advanced but",
    "b1",
    "b2",
    "c1",
    "conversational level",
    "can hold a conversation",
]

# Low-signal exclusion keywords
# Posts containing these are filtered out (test-focused, academic, off-topic)
EXCLUDE_KEYWORDS: list[str] = [
    # === Language proficiency tests ===
    "jlpt",
    "n1",
    "n2",
    "n3",
    "n4",
    "n5",
    "hsk",
    "topik",
    "dele",
    "delf",
    "dalf",
    "goethe",
    "telc",
    "cils",
    "celi",
    "toefl",
    "ielts",
    "test prep",
    "exam prep",
    "passing the",
    "pass the exam",

    # === Academic/homework ===
    "homework",
    "assignment",
    "class assignment",
    "school project",
    "university course",
    "college course",
    "quiz",
    "final exam",
    "midterm",
    "grade",
    "grading",
    "professor",
    "teacher said",

    # === Translation requests ===
    "translate this",
    "what does this mean",
    "help me translate",
    "can someone translate",
    "translation help",
    "what does this say",
    "how do you say",

    # === Media consumption (passive) ===
    "anime",
    "manga",
    "light novel",
    "visual novel",
    "drama",
    "kdrama",
    "cdrama",
    "jdrama",
    "subtitles",
    "watch without subs",
    "raw anime",
    "webtoon",

    # === Off-topic ===
    "tattoo",
    "song lyrics",
    "lyrics translation",
    "game translation",
    "meme",
    "joke translation",

    # === Resource requests (not conversation-focused) ===
    "best textbook",
    "textbook recommendation",
    "anki deck",
    "flashcard",
    "grammar guide",
    "what app",
    "which app",
    "youtube channel",
    "podcast recommendation",
]


def has_trigger_keyword(text: str) -> tuple[bool, list[str]]:
    """
    Check if text contains any trigger keywords.
    Returns (has_trigger, list_of_matched_keywords).
    """
    text_lower = text.lower()
    matched = [kw for kw in TRIGGER_KEYWORDS if kw in text_lower]
    return len(matched) > 0, matched


def has_exclude_keyword(text: str) -> tuple[bool, list[str]]:
    """
    Check if text contains any exclusion keywords.
    Returns (should_exclude, list_of_matched_keywords).
    """
    text_lower = text.lower()
    matched = [kw for kw in EXCLUDE_KEYWORDS if kw in text_lower]
    return len(matched) > 0, matched


if __name__ == "__main__":
    print("Keyword Configuration")
    print("=" * 50)
    print(f"Trigger keywords: {len(TRIGGER_KEYWORDS)}")
    print(f"Exclusion keywords: {len(EXCLUDE_KEYWORDS)}")

    # Test examples
    print("\n" + "=" * 50)
    print("Test Examples:")
    print("=" * 50)

    test_posts = [
        "I've been learning Japanese for 2 years but I freeze up when talking to my in-laws",
        "Need help with JLPT N3 grammar",
        "Can someone translate this anime scene?",
        "Moving to Spain next month and scared to speak with locals",
        "Best Anki deck for Korean vocabulary?",
        "Frustrated that I can read French but can't speak it",
    ]

    for post in test_posts:
        has_trigger, triggers = has_trigger_keyword(post)
        has_exclude, excludes = has_exclude_keyword(post)

        print(f"\nPost: \"{post[:60]}...\"" if len(post) > 60 else f"\nPost: \"{post}\"")
        print(f"  Triggers: {triggers if triggers else 'None'}")
        print(f"  Excludes: {excludes if excludes else 'None'}")
        print(f"  Result: {'KEEP' if has_trigger and not has_exclude else 'SKIP'}")
