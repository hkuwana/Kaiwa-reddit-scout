"""
Response draft generator for Reddit leads using Gemini.
"""

import logging
from typing import Optional

from src.analyzer.gemini_client import GeminiClient
from src.storage.models import Lead

logger = logging.getLogger(__name__)

# Public comment prompt
PUBLIC_DRAFT_PROMPT = """You are helping draft a supportive public comment on Reddit for someone struggling with language learning, specifically speaking practice.

POST DETAILS:
- Subreddit: r/{subreddit}
- Title: {title}
- Body: {body}
- Category: {category}

Write a helpful, empathetic Reddit comment that:
1. Acknowledges their specific struggle (speaking anxiety, lack of practice, etc.)
2. Shares a brief relatable insight or tip
3. Subtly mentions that AI conversation apps can help with low-pressure speaking practice
4. Does NOT directly promote Kaiwa or any specific app - keep it natural and helpful
5. Keeps it under 150 words
6. Sounds like a friendly Redditor, not a marketer

Write ONLY the comment text, no explanations or headers.
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

    def generate_public_draft(self, lead: Lead) -> Optional[str]:
        """
        Generate a public comment draft for a lead.

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

        return self.client.generate(prompt, max_tokens=300)

    def generate_dm_draft(self, lead: Lead) -> Optional[str]:
        """
        Generate a DM draft for a lead.

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

        return self.client.generate(prompt, max_tokens=200)

    def generate_responses(self, lead: Lead) -> Lead:
        """
        Generate both public and DM drafts for a lead.

        Args:
            lead: Lead to generate responses for

        Returns:
            Lead with updated public_draft and dm_draft fields
        """
        if not self.client.is_configured():
            logger.debug("Gemini not configured - skipping response generation")
            return lead

        logger.info(f"Generating responses for lead {lead.post_id}...")

        lead.public_draft = self.generate_public_draft(lead)
        lead.dm_draft = self.generate_dm_draft(lead)

        return lead

    def generate_responses_batch(self, leads: list[Lead]) -> list[Lead]:
        """
        Generate responses for multiple leads.

        Args:
            leads: List of leads

        Returns:
            Leads with generated responses
        """
        if not self.client.is_configured():
            logger.warning("Gemini not configured - returning leads without responses")
            return leads

        for i, lead in enumerate(leads):
            logger.info(f"Generating responses {i + 1}/{len(leads)}...")
            self.generate_responses(lead)

        return leads


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
