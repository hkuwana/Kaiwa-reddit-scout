"""
Signal scoring for Reddit leads using Gemini.
"""

import json
import logging
from typing import Optional

from src.analyzer.gemini_client import GeminiClient
from src.config.settings import gemini_config
from src.storage.models import Lead

logger = logging.getLogger(__name__)

# Scoring prompt template
SCORING_PROMPT = """You are analyzing a Reddit post to determine if this person is a good lead for Kaiwa, a language learning app that helps people practice speaking with AI tutors.

Analyze the following post and rate it as a potential lead.

POST DETAILS:
- Subreddit: r/{subreddit}
- Title: {title}
- Body: {body}
- Matched keywords: {triggers}

SCORING CRITERIA:
- Score 8-10 (HIGH): User explicitly expresses speaking anxiety, fear of conversation, or frustration with lack of speaking practice. They're actively seeking solutions.
- Score 5-7 (MEDIUM): User mentions language learning challenges that could relate to speaking, but it's not their main focus.
- Score 1-4 (LOW): User's post is about language learning but unlikely to benefit from a speaking practice app (grammar questions, resource sharing, etc.)

CATEGORIES (pick the most relevant):
- "Speaking Anxiety" - Fear of speaking, nervousness, embarrassment
- "Practice Gap" - Lacks conversation partners or practice opportunities
- "Immersion Prep" - Moving abroad, meeting in-laws, travel upcoming
- "Plateau Frustration" - Stuck at a level, not progressing
- "App Fatigue" - Frustrated with current apps like Duolingo
- "General Learning" - General language learning discussion

Respond with ONLY a JSON object in this exact format:
{{"score": <1-10>, "signal_type": "<HIGH|MEDIUM|LOW>", "category": "<category>", "reasoning": "<brief explanation>"}}
"""


class SignalScorer:
    """Score leads based on signal strength using Gemini."""

    def __init__(self, client: Optional[GeminiClient] = None):
        """
        Initialize scorer.

        Args:
            client: Gemini client (default: global client)
        """
        self.client = client or GeminiClient()
        self.threshold = gemini_config.signal_threshold

    def score_lead(self, lead: Lead) -> Lead:
        """
        Score a single lead and update its fields.

        Args:
            lead: Lead to score

        Returns:
            Lead with updated signal_score, signal_type, and category
        """
        if not self.client.is_configured():
            logger.debug("Gemini not configured - skipping scoring")
            return lead

        prompt = SCORING_PROMPT.format(
            subreddit=lead.subreddit,
            title=lead.title,
            body=lead.body[:1000],  # Truncate long posts
            triggers=", ".join(lead.matched_triggers),
        )

        try:
            response = self.client.generate_json(prompt)
            if not response:
                return lead

            result = json.loads(response)

            lead.signal_score = result.get("score", 5)
            lead.signal_type = result.get("signal_type", "MEDIUM")
            lead.category = result.get("category", "General Learning")

            logger.info(
                f"Scored lead {lead.post_id}: {lead.signal_score}/10 ({lead.signal_type}) - {lead.category}"
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse scoring response: {e}")
        except Exception as e:
            logger.error(f"Error scoring lead: {e}")

        return lead

    def score_leads(self, leads: list[Lead]) -> list[Lead]:
        """
        Score multiple leads.

        Args:
            leads: List of leads to score

        Returns:
            List of scored leads
        """
        if not self.client.is_configured():
            logger.warning("Gemini not configured - returning leads unscored")
            return leads

        scored = []
        for i, lead in enumerate(leads):
            logger.info(f"Scoring lead {i + 1}/{len(leads)}...")
            scored_lead = self.score_lead(lead)
            scored.append(scored_lead)

        return scored

    def filter_high_signal(self, leads: list[Lead]) -> list[Lead]:
        """
        Filter leads to only high-signal ones above threshold.

        Args:
            leads: List of scored leads

        Returns:
            Leads with signal_score >= threshold
        """
        return [
            lead for lead in leads
            if lead.signal_score is not None and lead.signal_score >= self.threshold
        ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from src.storage.models import RedditPost

    print("Testing Signal Scorer")
    print("=" * 50)

    # Create a sample lead
    sample_post = RedditPost(
        id="test123",
        subreddit="languagelearning",
        author="anxious_learner",
        title="I freeze up every time I try to speak Japanese",
        selftext="I've been studying for 2 years with textbooks and Duolingo, but the moment someone speaks to me I panic and forget everything. My wife's family is Japanese and I feel so embarrassed at family gatherings...",
        url="https://reddit.com/r/languagelearning/test123",
        permalink="/r/languagelearning/comments/test123/test/",
        created_utc=1702800000.0,
        score=42,
        num_comments=15,
    )

    lead = Lead.from_post(
        sample_post,
        matched_triggers=["freeze up", "embarrassed", "family"],
        language_detected="ja",
    )

    scorer = SignalScorer()
    print(f"Gemini configured: {scorer.client.is_configured()}")

    if scorer.client.is_configured():
        scored_lead = scorer.score_lead(lead)
        print(f"\nScoring Result:")
        print(f"  Score: {scored_lead.signal_score}/10")
        print(f"  Type: {scored_lead.signal_type}")
        print(f"  Category: {scored_lead.category}")
    else:
        print("\nSkipping test - Gemini not configured")
