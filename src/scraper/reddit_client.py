"""
Reddit API client using PRAW.
"""

import logging
from typing import Iterator, Optional

import praw
from praw.models import Submission

from src.config.settings import reddit_config
from src.storage.models import RedditPost

logger = logging.getLogger(__name__)


class RedditClient:
    """Wrapper around PRAW for Reddit API access."""

    def __init__(self):
        """Initialize Reddit client with credentials from config."""
        if not reddit_config.is_valid():
            raise ValueError(
                "Reddit API credentials not configured. "
                "Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env"
            )

        self.reddit = praw.Reddit(
            client_id=reddit_config.client_id,
            client_secret=reddit_config.client_secret,
            user_agent=reddit_config.user_agent,
            username=reddit_config.username,
            password=reddit_config.password,
        )
        logger.info(f"Reddit client initialized (read_only={self.reddit.read_only})")

    def _submission_to_post(self, submission: Submission) -> RedditPost:
        """Convert PRAW Submission to our RedditPost model."""
        return RedditPost(
            id=submission.id,
            subreddit=str(submission.subreddit),
            author=str(submission.author) if submission.author else "[deleted]",
            title=submission.title,
            selftext=submission.selftext or "",
            url=submission.url,
            permalink=submission.permalink,
            created_utc=submission.created_utc,
            score=submission.score,
            num_comments=submission.num_comments,
        )

    def get_new_posts(
        self,
        subreddits: list[str],
        limit: int = 100,
        time_filter: str = "day",
    ) -> Iterator[RedditPost]:
        """
        Fetch new posts from specified subreddits.

        Args:
            subreddits: List of subreddit names to search
            limit: Maximum posts to fetch per subreddit
            time_filter: Time filter for 'top' sorting (hour, day, week, month, year, all)

        Yields:
            RedditPost objects
        """
        # Combine subreddits with + for multi-subreddit query
        multi_sub = "+".join(subreddits)
        subreddit = self.reddit.subreddit(multi_sub)

        logger.info(f"Fetching up to {limit} new posts from r/{multi_sub}")

        count = 0
        for submission in subreddit.new(limit=limit):
            try:
                post = self._submission_to_post(submission)
                yield post
                count += 1
            except Exception as e:
                logger.warning(f"Error processing submission {submission.id}: {e}")
                continue

        logger.info(f"Fetched {count} posts")

    def get_hot_posts(
        self,
        subreddits: list[str],
        limit: int = 100,
    ) -> Iterator[RedditPost]:
        """Fetch hot posts from specified subreddits."""
        multi_sub = "+".join(subreddits)
        subreddit = self.reddit.subreddit(multi_sub)

        logger.info(f"Fetching up to {limit} hot posts from r/{multi_sub}")

        count = 0
        for submission in subreddit.hot(limit=limit):
            try:
                post = self._submission_to_post(submission)
                yield post
                count += 1
            except Exception as e:
                logger.warning(f"Error processing submission {submission.id}: {e}")
                continue

        logger.info(f"Fetched {count} posts")

    def search_posts(
        self,
        subreddits: list[str],
        query: str,
        limit: int = 100,
        time_filter: str = "week",
        sort: str = "new",
    ) -> Iterator[RedditPost]:
        """
        Search posts in subreddits matching a query.

        Args:
            subreddits: List of subreddit names
            query: Search query string
            limit: Maximum results
            time_filter: Time filter (hour, day, week, month, year, all)
            sort: Sort order (relevance, hot, top, new, comments)

        Yields:
            RedditPost objects
        """
        multi_sub = "+".join(subreddits)
        subreddit = self.reddit.subreddit(multi_sub)

        logger.info(f"Searching r/{multi_sub} for '{query}' (limit={limit})")

        count = 0
        for submission in subreddit.search(
            query, sort=sort, time_filter=time_filter, limit=limit
        ):
            try:
                post = self._submission_to_post(submission)
                yield post
                count += 1
            except Exception as e:
                logger.warning(f"Error processing submission {submission.id}: {e}")
                continue

        logger.info(f"Found {count} posts matching '{query}'")


class MockRedditClient:
    """Mock client for testing without API credentials."""

    def __init__(self):
        logger.info("Using MockRedditClient (no API credentials)")

    def get_new_posts(
        self,
        subreddits: list[str],
        limit: int = 100,
        time_filter: str = "day",
    ) -> Iterator[RedditPost]:
        """Return sample posts for testing."""
        sample_posts = [
            RedditPost(
                id="test1",
                subreddit="languagelearning",
                author="anxious_learner",
                title="Scared to speak Japanese with my in-laws visiting next month",
                selftext="I've been learning Japanese for 2 years using Duolingo and textbooks, but I freeze up completely when trying to speak. My wife's parents are visiting from Tokyo next month and I'm terrified. Any advice?",
                url="https://reddit.com/r/languagelearning/test1",
                permalink="/r/languagelearning/comments/test1/scared_to_speak/",
                created_utc=1702800000.0,
                score=45,
                num_comments=23,
            ),
            RedditPost(
                id="test2",
                subreddit="LearnJapanese",
                author="jlpt_student",
                title="Best resources for JLPT N3 grammar?",
                selftext="Taking the test in July, need textbook recommendations.",
                url="https://reddit.com/r/LearnJapanese/test2",
                permalink="/r/LearnJapanese/comments/test2/jlpt_n3/",
                created_utc=1702790000.0,
                score=12,
                num_comments=8,
            ),
            RedditPost(
                id="test3",
                subreddit="learnspanish",
                author="moving_soon",
                title="Moving to Barcelona in 3 months - frustrated I still can't speak",
                selftext="I've been using apps for a year but I'm still afraid to speak with actual people. I can read pretty well but conversation terrifies me. Has anyone overcome this?",
                url="https://reddit.com/r/learnspanish/test3",
                permalink="/r/learnspanish/comments/test3/moving_barcelona/",
                created_utc=1702780000.0,
                score=67,
                num_comments=31,
            ),
            RedditPost(
                id="test4",
                subreddit="Korean",
                author="kdrama_fan",
                title="Can someone translate this kdrama scene?",
                selftext="I don't understand what they're saying at 32:15 in episode 5.",
                url="https://reddit.com/r/Korean/test4",
                permalink="/r/Korean/comments/test4/translate_kdrama/",
                created_utc=1702770000.0,
                score=5,
                num_comments=3,
            ),
            RedditPost(
                id="test5",
                subreddit="French",
                author="expat_france",
                title="Been learning French for years but can't hold a conversation",
                selftext="Frustrated because I understand everything when reading and can even watch movies without subtitles, but when someone speaks to me I blank out and can't respond. My partner's family thinks I'm rude because I barely speak at dinners. Anyone else experience this?",
                url="https://reddit.com/r/French/test5",
                permalink="/r/French/comments/test5/cant_speak/",
                created_utc=1702760000.0,
                score=89,
                num_comments=45,
            ),
        ]

        for post in sample_posts[:limit]:
            yield post

    def get_hot_posts(self, subreddits: list[str], limit: int = 100) -> Iterator[RedditPost]:
        return self.get_new_posts(subreddits, limit)

    def search_posts(self, subreddits: list[str], query: str, **kwargs) -> Iterator[RedditPost]:
        return self.get_new_posts(subreddits, kwargs.get("limit", 100))


def get_reddit_client(use_mock: bool = False) -> RedditClient | MockRedditClient:
    """
    Factory function to get appropriate Reddit client.

    Args:
        use_mock: Force use of mock client for testing

    Returns:
        RedditClient or MockRedditClient
    """
    if use_mock:
        return MockRedditClient()

    if reddit_config.is_valid():
        return RedditClient()
    else:
        logger.warning("Reddit credentials not configured, using mock client")
        return MockRedditClient()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing Reddit Client")
    print("=" * 50)

    # Use mock client for testing without credentials
    client = get_reddit_client(use_mock=True)

    print("\nFetching sample posts:")
    for post in client.get_new_posts(["languagelearning"], limit=5):
        print(f"\n  [{post.subreddit}] u/{post.author}")
        print(f"  Title: {post.title[:60]}...")
        print(f"  URL: {post.direct_url}")
