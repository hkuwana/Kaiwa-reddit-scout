"""
Signal scoring for Reddit leads using Gemini.
"""

import json
import logging
import time
from typing import Optional

from src.analyzer.gemini_client import GeminiClient
from src.config.settings import gemini_config
from src.storage.models import Lead

logger = logging.getLogger(__name__)

# Scoring prompt template for single lead
SCORING_PROMPT = """You are analyzing a Reddit post to determine if this person is a good lead for Kaiwa, a language learning app that helps people practice speaking with AI tutors.

Analyze the following post and rate it as a potential lead.

POST DETAILS:
- Subreddit: r/{subreddit}
- Title: {title}
- Body: {body}
- Matched keywords: {triggers}

SCORING CRITERIA (with adjustments for urgency and willingness to pay):
- BASE SCORE: Start with psychological need assessment
- +3 POINTS if mentions job/relocation/visa requirement (high urgency, high stakes)
- +2 POINTS if mentions tutor costs or paid alternatives (price-conscious, willing to pay)
- +2 POINTS if mentions embarrassment/anxiety in real situations (emotional pain)
- -5 POINTS if asks for "free" resources or alternatives (will never pay)

FINAL SCORE:
- Score 8-10 (HIGH): Strong speaking anxiety OR urgent deadline (job/relocation) OR willing to pay. Actively seeking solutions.
- Score 5-7 (MEDIUM): Some speaking challenges but no urgency or payment willingness signals.
- Score 1-4 (LOW): General learning, free hunters, or unlikely to benefit from speaking practice app.

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

# Batch scoring prompt for multiple leads
BATCH_SCORING_PROMPT = """You are analyzing multiple Reddit posts to determine if these people are good leads for Kaiwa, a language learning app that helps people practice speaking with AI tutors.

Analyze each post and rate it as a potential lead.

SCORING CRITERIA (adjust for urgency and willingness to pay):
- +3 POINTS for job/relocation/visa urgency
- +2 POINTS for tutor cost complaints (willing to pay)
- +2 POINTS for anxiety/embarrassment in real situations
- -5 POINTS for "free" resource requests (will never pay)

SCORES:
- 8-10 (HIGH): Speaking anxiety OR urgent deadline OR willing to pay
- 5-7 (MEDIUM): Some challenges but no urgency/payment signals
- 1-4 (LOW): General learning or free hunters

CATEGORIES: "Speaking Anxiety", "Practice Gap", "Immersion Prep", "Plateau Frustration", "App Fatigue", "General Learning"

POSTS TO ANALYZE:
{posts_json}

Respond with ONLY a JSON array containing one object per post, in the same order:
[{{"id": "<post_id>", "score": <1-10>, "signal_type": "<HIGH|MEDIUM|LOW>", "category": "<category>", "reasoning": "<brief explanation>"}}, ...]
"""


class SignalScorer:
    """Score leads based on signal strength using Gemini."""

    def __init__(self, client: Optional[GeminiClient] = None, batch_size: int = 5):
        """
        Initialize scorer.

        Args:
            client: Gemini client (default: global client)
            batch_size: Number of leads to process in a single API call
        """
        self.client = client or GeminiClient()
        self.threshold = gemini_config.signal_threshold
        self.batch_size = batch_size

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

    def _score_batch(self, leads: list[Lead]) -> list[Lead]:
        """
        Score a batch of leads in a single API call.

        Args:
            leads: List of leads to score (max batch_size)

        Returns:
            List of scored leads
        """
        if not leads:
            return leads

        # Prepare posts data for batch prompt
        posts_data = []
        for lead in leads:
            posts_data.append({
                "id": lead.post_id,
                "subreddit": lead.subreddit,
                "title": lead.title,
                "body": lead.body[:500],  # Shorter for batch
                "triggers": ", ".join(lead.matched_triggers[:5]),
            })

        prompt = BATCH_SCORING_PROMPT.format(posts_json=json.dumps(posts_data, indent=2))

        try:
            response = self.client.generate_json(prompt, max_tokens=2000)
            if not response:
                # Fallback to individual scoring
                logger.warning("Batch scoring failed, falling back to individual scoring")
                return [self.score_lead(lead) for lead in leads]

            results = json.loads(response)

            # Create a map of results by post_id
            results_map = {r.get("id"): r for r in results}

            # Update leads with scores
            for lead in leads:
                if lead.post_id in results_map:
                    result = results_map[lead.post_id]
                    lead.signal_score = result.get("score", 5)
                    lead.signal_type = result.get("signal_type", "MEDIUM")
                    lead.category = result.get("category", "General Learning")
                    logger.info(
                        f"Scored lead {lead.post_id}: {lead.signal_score}/10 ({lead.signal_type}) - {lead.category}"
                    )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse batch response: {e}, falling back to individual")
            return [self.score_lead(lead) for lead in leads]
        except Exception as e:
            logger.error(f"Error in batch scoring: {e}, falling back to individual")
            return [self.score_lead(lead) for lead in leads]

        return leads

    def score_leads(self, leads: list[Lead], use_batch: bool = True) -> list[Lead]:
        """
        Score multiple leads, optionally using batch processing.

        Args:
            leads: List of leads to score
            use_batch: Whether to use batch processing (default: True)

        Returns:
            List of scored leads
        """
        if not self.client.is_configured():
            logger.warning("Gemini not configured - returning leads unscored")
            return leads

        if not leads:
            return leads

        if use_batch and len(leads) > 1:
            logger.info(f"Batch scoring {len(leads)} leads (batch_size={self.batch_size})...")
            scored = []

            # Process in batches
            for i in range(0, len(leads), self.batch_size):
                batch = leads[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (len(leads) + self.batch_size - 1) // self.batch_size

                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} leads)...")
                scored_batch = self._score_batch(batch)
                scored.extend(scored_batch)

                # Small delay between batches to avoid rate limiting
                if i + self.batch_size < len(leads):
                    time.sleep(0.5)

            return scored
        else:
            # Individual scoring
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
