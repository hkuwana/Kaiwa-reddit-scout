"""
Language definitions and associated subreddits.
"""

from dataclasses import dataclass


@dataclass
class Language:
    """Language configuration."""
    code: str
    name: str
    native_name: str
    subreddits: list[str]


# All supported languages with their learning subreddits
LANGUAGES: dict[str, Language] = {
    "ja": Language(
        code="ja",
        name="Japanese",
        native_name="日本語",
        subreddits=["LearnJapanese", "japanese"],
    ),
    "en": Language(
        code="en",
        name="English",
        native_name="English",
        subreddits=["EnglishLearning", "ENGLISH"],
    ),
    "es": Language(
        code="es",
        name="Spanish",
        native_name="Español",
        subreddits=["learnspanish", "Spanish"],
    ),
    "fr": Language(
        code="fr",
        name="French",
        native_name="Français",
        subreddits=["French", "learnfrench"],
    ),
    "de": Language(
        code="de",
        name="German",
        native_name="Deutsch",
        subreddits=["German", "learngerman"],
    ),
    "it": Language(
        code="it",
        name="Italian",
        native_name="Italiano",
        subreddits=["italianlearning", "Italian"],
    ),
    "pt": Language(
        code="pt",
        name="Portuguese",
        native_name="Português",
        subreddits=["Portuguese", "learnportuguese"],
    ),
    "ko": Language(
        code="ko",
        name="Korean",
        native_name="한국어",
        subreddits=["Korean", "hanguk"],
    ),
    "zh": Language(
        code="zh",
        name="Chinese",
        native_name="中文",
        subreddits=["ChineseLanguage", "Chinese", "MandarinChinese"],
    ),
    "hi": Language(
        code="hi",
        name="Hindi",
        native_name="हिन्दी",
        subreddits=["Hindi", "learnHindi"],
    ),
    "ru": Language(
        code="ru",
        name="Russian",
        native_name="Русский",
        subreddits=["Russian", "learnRussian"],
    ),
    "vi": Language(
        code="vi",
        name="Vietnamese",
        native_name="Tiếng Việt",
        subreddits=["Vietnamese", "learnVietnamese"],
    ),
    "nl": Language(
        code="nl",
        name="Dutch",
        native_name="Nederlands",
        subreddits=["LearnDutch", "Dutch"],
    ),
    "fil": Language(
        code="fil",
        name="Filipino",
        native_name="Filipino",
        subreddits=["Tagalog", "Filipino"],
    ),
    "id": Language(
        code="id",
        name="Indonesian",
        native_name="Bahasa Indonesia",
        subreddits=["Indonesian", "learnIndonesian"],
    ),
    "tr": Language(
        code="tr",
        name="Turkish",
        native_name="Türkçe",
        subreddits=["turkishlearning", "Turkish"],
    ),
}

# Priority languages - Top 7 high-potential markets
PRIORITY_LANGUAGES = ["fr", "en", "es", "ja", "de", "zh", "ko"]

# Relocation cluster - High-stakes subreddits for people with urgency and money
RELOCATION_SUBREDDITS = [
    "expats",
    "IWantOut",
    "digitalnomad",
    "movingtojapan",
    "japanlife",
    "movingtogermany",
    "germany",
    "askFrance",
    "movetocanada",
    "IWantToLeaveTheUS",
    "AmericanExpats",
    "chinalife",
    "Beijing",
    "Shanghai",
    "korea",
    "Living_in_Korea",
]

# K-pop and cultural interest subreddits (high engagement, willing to invest)
CULTURAL_SUBREDDITS = [
    "kpop",
    "kpophelp",
    "Korean",
]

# General language learning subreddits (not language-specific)
GENERAL_SUBREDDITS = [
    "languagelearning",
    "language_exchange",
    "polyglot",
]


def get_all_subreddits() -> list[str]:
    """Get all subreddits to monitor (includes relocation and cultural subreddits)."""
    subreddits = set(GENERAL_SUBREDDITS)
    subreddits.update(RELOCATION_SUBREDDITS)
    subreddits.update(CULTURAL_SUBREDDITS)
    # Add language-specific subreddits for priority languages only
    for code in PRIORITY_LANGUAGES:
        if code in LANGUAGES:
            subreddits.update(LANGUAGES[code].subreddits)
    return sorted(subreddits)


def get_language_names() -> list[str]:
    """Get all language names for keyword matching."""
    names = []
    for lang in LANGUAGES.values():
        names.append(lang.name.lower())
        names.append(lang.native_name.lower())
    return names


def detect_language(text: str) -> str | None:
    """
    Detect which language is being discussed in the text.
    Returns language code or None (only detects priority languages).
    """
    text_lower = text.lower()
    # Only detect priority languages
    for code in PRIORITY_LANGUAGES:
        if code in LANGUAGES:
            lang = LANGUAGES[code]
            if lang.name.lower() in text_lower or lang.native_name.lower() in text_lower:
                return code
    return None


if __name__ == "__main__":
    print("Supported Languages:")
    print("-" * 50)
    for code, lang in LANGUAGES.items():
        print(f"  [{code}] {lang.name} ({lang.native_name})")
        print(f"       Subreddits: {', '.join(lang.subreddits)}")

    print("\nGeneral Subreddits:")
    print(f"  {', '.join(GENERAL_SUBREDDITS)}")

    print(f"\nTotal subreddits to monitor: {len(get_all_subreddits())}")
    print(f"Subreddits: {', '.join(get_all_subreddits())}")
