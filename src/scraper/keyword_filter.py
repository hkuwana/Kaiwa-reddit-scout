"""
Keyword-based filtering for Reddit posts.
"""

import logging
from dataclasses import dataclass
from typing import Iterator, Optional

from src.config.keywords import has_trigger_keyword, has_exclude_keyword
from src.config.languages import detect_language
from src.storage.models import RedditPost, Lead

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    """Result of filtering a post."""
    post: RedditPost
    passed: bool
    matched_triggers: list[str]
    matched_excludes: list[str]
    language_detected: Optional[str]
    reason: str


class KeywordFilter:
    """Filter Reddit posts based on trigger and exclusion keywords."""

    def __init__(self, require_trigger: bool = True, exclude_on_match: bool = True):
        """
        Initialize the filter.

        Args:
            require_trigger: Post must have at least one trigger keyword
            exclude_on_match: Exclude posts with any exclusion keywords
        """
        self.require_trigger = require_trigger
        self.exclude_on_match = exclude_on_match
        self.stats = {
            "total": 0,
            "passed": 0,
            "no_trigger": 0,
            "excluded": 0,
            "deleted_author": 0,
        }

    def filter_post(self, post: RedditPost) -> FilterResult:
        """
        Apply keyword filtering to a single post.

        Returns:
            FilterResult with pass/fail status and details
        """
        self.stats["total"] += 1
        text = post.full_text

        # Skip deleted authors
        if post.author == "[deleted]":
            self.stats["deleted_author"] += 1
            return FilterResult(
                post=post,
                passed=False,
                matched_triggers=[],
                matched_excludes=[],
                language_detected=None,
                reason="deleted_author",
            )

        # Check for exclusion keywords first (save processing)
        has_exclude, excludes = has_exclude_keyword(text)
        if self.exclude_on_match and has_exclude:
            self.stats["excluded"] += 1
            return FilterResult(
                post=post,
                passed=False,
                matched_triggers=[],
                matched_excludes=excludes,
                language_detected=None,
                reason=f"excluded: {', '.join(excludes[:3])}",
            )

        # Check for trigger keywords
        has_trigger, triggers = has_trigger_keyword(text)
        if self.require_trigger and not has_trigger:
            self.stats["no_trigger"] += 1
            return FilterResult(
                post=post,
                passed=False,
                matched_triggers=[],
                matched_excludes=[],
                language_detected=None,
                reason="no_trigger",
            )

        # Detect language
        language = detect_language(text)

        # Post passed all filters
        self.stats["passed"] += 1
        return FilterResult(
            post=post,
            passed=True,
            matched_triggers=triggers,
            matched_excludes=excludes,
            language_detected=language,
            reason="passed",
        )

    def filter_posts(self, posts: Iterator[RedditPost]) -> Iterator[Lead]:
        """
        Filter multiple posts and yield qualifying Leads.

        Args:
            posts: Iterator of RedditPost objects

        Yields:
            Lead objects for posts that pass filtering
        """
        for post in posts:
            result = self.filter_post(post)

            if result.passed:
                lead = Lead.from_post(
                    post,
                    matched_triggers=result.matched_triggers,
                    language_detected=result.language_detected,
                )
                logger.debug(
                    f"Lead found: u/{lead.author} in r/{lead.subreddit} "
                    f"(triggers: {result.matched_triggers})"
                )
                yield lead
            else:
                logger.debug(f"Filtered out: {post.id} - {result.reason}")

    def get_stats(self) -> dict:
        """Get filtering statistics."""
        return {
            **self.stats,
            "pass_rate": (
                f"{self.stats['passed'] / self.stats['total'] * 100:.1f}%"
                if self.stats["total"] > 0
                else "N/A"
            ),
        }

    def print_stats(self):
        """Print filtering statistics."""
        stats = self.get_stats()
        print("\nFilter Statistics:")
        print("-" * 30)
        print(f"  Total processed: {stats['total']}")
        print(f"  Passed (leads):  {stats['passed']}")
        print(f"  No trigger:      {stats['no_trigger']}")
        print(f"  Excluded:        {stats['excluded']}")
        print(f"  Deleted author:  {stats['deleted_author']}")
        print(f"  Pass rate:       {stats['pass_rate']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    from src.scraper.reddit_client import get_reddit_client

    print("Testing Keyword Filter")
    print("=" * 50)

    # Get mock posts
    client = get_reddit_client(use_mock=True)
    posts = list(client.get_new_posts(["languagelearning"], limit=10))

    # Apply filter
    keyword_filter = KeywordFilter()

    print("\nFiltering posts:")
    print("-" * 50)

    leads = []
    for post in posts:
        result = keyword_filter.filter_post(post)
        status = "PASS" if result.passed else "SKIP"
        print(f"\n[{status}] u/{post.author}: {post.title[:50]}...")

        if result.passed:
            print(f"       Triggers: {result.matched_triggers}")
            print(f"       Language: {result.language_detected}")
            leads.append(Lead.from_post(post, result.matched_triggers, result.language_detected))
        else:
            print(f"       Reason: {result.reason}")

    keyword_filter.print_stats()

    print(f"\n\nQualified Leads: {len(leads)}")
    for lead in leads:
        print(f"  - u/{lead.author} ({lead.language_detected}): {lead.title[:40]}...")
