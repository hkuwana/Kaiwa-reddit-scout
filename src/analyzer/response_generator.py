"""
Response draft generator for Reddit leads using Gemini.
"""

import json
import logging
from typing import Optional

from src.analyzer.gemini_client import GeminiClient
from src.config.settings import gemini_config
from src.storage.models import Lead

logger = logging.getLogger(__name__)

# Comment worthiness evaluation prompt
COMMENT_WORTHY_PROMPT = """Evaluate if this Reddit post is worth commenting on for a language learning app that helps with speaking practice.

POST DETAILS:
- Subreddit: r/{subreddit}
- Title: {title}
- Body: {body}
- Signal score: {signal_score}/10
- Category: {category}

CRITERIA FOR WORTH COMMENTING:
1. The user has a SPECIFIC, ACTIONABLE problem we can help with (not just venting)
2. They're open to suggestions (asking for advice, not just sharing frustration)
3. A genuine, helpful comment would feel natural and not out of place
4. The post hasn't already been solved or is too old/inactive
5. Our comment could add unique value (not just repeating what others said)

NOT WORTH COMMENTING IF:
- User is just celebrating/venting without seeking help
- Very short post with no real substance to engage with
- Too general/vague to give meaningful advice
- Asking about grammar/vocabulary (not speaking practice)
- Looking for specific resources we can't provide (tutors in a city, etc.)
- Already received comprehensive answers

Respond with ONLY a JSON object:
{{"worthy": true/false, "reason": "<brief 1-sentence explanation>"}}
"""

# Public comment prompt
PUBLIC_DRAFT_PROMPT = """Write a SHORT Reddit comment (2-3 sentences MAX) responding to this post.

POST:
r/{subreddit}: {title}
{body}

RULES:
- 2-3 sentences MAX, be concise
- Share ONE quick tip or relatable experience
- End with a genuine question to start a conversation (about their situation, not leading anywhere)
- Sound like a normal person, not a marketer
- NO emojis, NO *italics* or **bold**
- NO em dashes (use commas or periods instead)
- NO "Hey!" or enthusiastic greetings
- NO "You've got this!" or cheerleader phrases
- NO mentioning apps, AI, tools, or products
- Use simple punctuation (periods, commas, question marks)

Write ONLY the comment, nothing else.
"""

# DM prompt
DM_DRAFT_PROMPT = """You are helping draft a friendly direct message to a Reddit user who might benefit from a language speaking practice app.

USER CONTEXT:
- Their post: "{title}"
- Their struggle: {category}
- Language they're learning: {language}

Write a warm, personal DM that:
1. References their specific post and struggle
2. Mentions you're working on Kaiwa, an app for speaking practice with AI tutors
3. Offers to let them try it for free to see if it helps
4. Keeps it short (under 100 words)
5. Sounds genuine and helpful, not salesy
6. Ends with a low-pressure invitation

Write ONLY the message text, no subject line or explanations.
"""


class ResponseGenerator:
    """Generate response drafts for Reddit leads using Gemini."""

    def __init__(self, client: Optional[GeminiClient] = None):
        """
        Initialize generator.

        Args:
            client: Gemini client (default: global client)
        """
        self.client = client or GeminiClient()
        self.response_model = gemini_config.response_model
        self.require_comment_worthy = gemini_config.require_comment_worthy

    def evaluate_comment_worthy(self, lead: Lead) -> tuple[bool, str]:
        """
        Evaluate if a lead is worth commenting on.

        Uses the scoring model (cheaper/faster) for this evaluation.

        Args:
            lead: Lead to evaluate

        Returns:
            Tuple of (is_worthy, reason)
        """
        if not self.client.is_configured():
            return True, "Skipped evaluation - API not configured"

        prompt = COMMENT_WORTHY_PROMPT.format(
            subreddit=lead.subreddit,
            title=lead.title,
            body=lead.body[:1000],
            signal_score=lead.signal_score or "N/A",
            category=lead.category or "General Learning",
        )

        try:
            # Use default model (Gemma) for evaluation - it's cheaper
            response = self.client.generate_json(prompt, max_tokens=200)
            if not response:
                return True, "Evaluation failed - defaulting to worthy"

            result = json.loads(response)
            worthy = result.get("worthy", True)
            reason = result.get("reason", "No reason provided")

            logger.info(f"Comment worthy evaluation for {lead.post_id}: {worthy} - {reason}")
            return worthy, reason

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse worthiness response: {e}")
            return True, "Parse error - defaulting to worthy"
        except Exception as e:
            logger.error(f"Error evaluating comment worthiness: {e}")
            return True, "Error - defaulting to worthy"

    def generate_public_draft(self, lead: Lead) -> Optional[str]:
        """
        Generate a public comment draft for a lead.

        Uses the response model (higher quality) for generation.

        Args:
            lead: Lead to generate comment for

        Returns:
            Draft comment text or None
        """
        if not self.client.is_configured():
            return None

        prompt = PUBLIC_DRAFT_PROMPT.format(
            subreddit=lead.subreddit,
            title=lead.title,
            body=lead.body[:1000],
            category=lead.category or "General Learning",
        )

        # Use response_model for better quality output
        return self.client.generate(prompt, max_tokens=300, model=self.response_model)

    def generate_dm_draft(self, lead: Lead) -> Optional[str]:
        """
        Generate a DM draft for a lead.

        Uses the response model (higher quality) for generation.

        Args:
            lead: Lead to generate DM for

        Returns:
            Draft DM text or None
        """
        if not self.client.is_configured():
            return None

        prompt = DM_DRAFT_PROMPT.format(
            title=lead.title,
            category=lead.category or "language learning challenges",
            language=lead.language_detected or "a new language",
        )

        # Use response_model for better quality output
        return self.client.generate(prompt, max_tokens=200, model=self.response_model)

    def generate_responses(self, lead: Lead) -> Lead:
        """
        Generate both public and DM drafts for a lead.

        First evaluates if the lead is worth commenting on (if enabled),
        then generates responses only for worthy leads.

        Args:
            lead: Lead to generate responses for

        Returns:
            Lead with updated fields (comment_worthy, public_draft, dm_draft)
        """
        if not self.client.is_configured():
            logger.debug("Gemini not configured - skipping response generation")
            return lead

        logger.info(f"Processing lead {lead.post_id}...")

        # Evaluate comment worthiness first (if enabled)
        if self.require_comment_worthy:
            worthy, reason = self.evaluate_comment_worthy(lead)
            lead.comment_worthy = worthy
            lead.comment_worthy_reason = reason

            if not worthy:
                logger.info(f"Skipping lead {lead.post_id} - not worth commenting: {reason}")
                return lead

        # Generate responses only for worthy leads
        logger.info(f"Generating responses for lead {lead.post_id} using {self.response_model}...")
        lead.public_draft = self.generate_public_draft(lead)
        lead.dm_draft = self.generate_dm_draft(lead)

        return lead

    def generate_responses_batch(self, leads: list[Lead]) -> tuple[list[Lead], int]:
        """
        Generate responses for multiple leads.

        Evaluates comment worthiness and only generates for worthy leads.

        Args:
            leads: List of leads

        Returns:
            Tuple of (leads with responses, count of skipped leads)
        """
        if not self.client.is_configured():
            logger.warning("Gemini not configured - returning leads without responses")
            return leads, 0

        skipped_count = 0
        for i, lead in enumerate(leads):
            logger.info(f"Processing lead {i + 1}/{len(leads)}...")
            self.generate_responses(lead)

            if lead.comment_worthy is False:
                skipped_count += 1

        worthy_count = len(leads) - skipped_count
        logger.info(f"Generated responses for {worthy_count} leads, skipped {skipped_count} as not comment-worthy")

        return leads, skipped_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from src.storage.models import RedditPost

    print("Testing Response Generator")
    print("=" * 50)

    # Create a sample lead
    sample_post = RedditPost(
        id="test123",
        subreddit="learnspanish",
        author="travel_learner",
        title="Moving to Madrid next month, terrified I can't hold a conversation",
        selftext="I've done Duolingo for a year but I panic when someone speaks Spanish to me. Any tips for getting more comfortable actually speaking?",
        url="https://reddit.com/r/learnspanish/test123",
        permalink="/r/learnspanish/comments/test123/test/",
        created_utc=1702800000.0,
        score=28,
        num_comments=12,
    )

    lead = Lead.from_post(
        sample_post,
        matched_triggers=["moving to", "terrified", "can't hold a conversation"],
        language_detected="es",
    )
    lead.category = "Immersion Prep"
    lead.signal_score = 9
    lead.signal_type = "HIGH"

    generator = ResponseGenerator()
    print(f"Gemini configured: {generator.client.is_configured()}")

    if generator.client.is_configured():
        lead = generator.generate_responses(lead)

        print("\n--- PUBLIC COMMENT DRAFT ---")
        print(lead.public_draft or "(not generated)")

        print("\n--- DM DRAFT ---")
        print(lead.dm_draft or "(not generated)")
    else:
        print("\nSkipping test - Gemini not configured")
