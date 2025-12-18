"""
Data models for Reddit leads.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class RedditPost:
    """Raw Reddit post/submission data."""
    id: str
    subreddit: str
    author: str
    title: str
    selftext: str
    url: str
    permalink: str
    created_utc: float
    score: int
    num_comments: int

    @property
    def full_text(self) -> str:
        """Combined title and body text."""
        return f"{self.title} {self.selftext}"

    @property
    def direct_url(self) -> str:
        """Full Reddit URL."""
        return f"https://reddit.com{self.permalink}"

    @property
    def message_url(self) -> str:
        """URL to send a direct message to the author."""
        return f"https://reddit.com/message/compose/?to={self.author}"

    @property
    def created_datetime(self) -> datetime:
        """Convert UTC timestamp to datetime."""
        return datetime.utcfromtimestamp(self.created_utc)


@dataclass
class Lead:
    """A filtered, qualified lead from Reddit."""
    # Post info
    post_id: str
    subreddit: str
    author: str
    title: str
    body: str
    post_url: str
    message_url: str
    created_at: datetime

    # Filter results
    matched_triggers: list[str] = field(default_factory=list)
    language_detected: Optional[str] = None

    # Metadata
    score: int = 0
    num_comments: int = 0
    scraped_at: datetime = field(default_factory=datetime.utcnow)

    # Phase 2 fields (AI analysis) - populated later
    signal_score: Optional[int] = None
    signal_type: Optional[str] = None  # HIGH, MEDIUM, LOW
    category: Optional[str] = None
    comment_worthy: Optional[bool] = None  # Whether this lead is worth commenting on
    comment_worthy_reason: Optional[str] = None  # Why or why not
    public_draft: Optional[str] = None
    dm_draft: Optional[str] = None

    # Status tracking
    status: str = "new"  # new, contacted, replied, converted, ignored

    @classmethod
    def from_post(
        cls,
        post: RedditPost,
        matched_triggers: list[str],
        language_detected: Optional[str] = None,
    ) -> "Lead":
        """Create a Lead from a RedditPost."""
        return cls(
            post_id=post.id,
            subreddit=post.subreddit,
            author=post.author,
            title=post.title,
            body=post.selftext,
            post_url=post.direct_url,
            message_url=post.message_url,
            created_at=post.created_datetime,
            matched_triggers=matched_triggers,
            language_detected=language_detected,
            score=post.score,
            num_comments=post.num_comments,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for CSV/JSON export."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data["created_at"] = self.created_at.isoformat()
        data["scraped_at"] = self.scraped_at.isoformat()
        # Convert list to comma-separated string
        data["matched_triggers"] = ", ".join(self.matched_triggers)
        return data

    def to_csv_row(self) -> dict:
        """Convert to a flat dict suitable for CSV."""
        return {
            "scraped_at": self.scraped_at.strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "subreddit": self.subreddit,
            "author": self.author,
            "title": self.title[:100],  # Truncate for readability
            "post_url": self.post_url,
            "message_url": self.message_url,
            "matched_triggers": ", ".join(self.matched_triggers),
            "language": self.language_detected or "",
            "score": self.score,
            "comments": self.num_comments,
            "status": self.status,
            # Phase 2: AI analysis fields
            "signal_score": self.signal_score or "",
            "signal_type": self.signal_type or "",
            "category": self.category or "",
            "comment_worthy": "" if self.comment_worthy is None else ("yes" if self.comment_worthy else "no"),
            "comment_worthy_reason": self.comment_worthy_reason or "",
            "public_draft": self.public_draft or "",
            "dm_draft": self.dm_draft or "",
        }


if __name__ == "__main__":
    # Test with sample data
    sample_post = RedditPost(
        id="abc123",
        subreddit="languagelearning",
        author="test_user",
        title="Scared to speak Japanese with my in-laws",
        selftext="I've been learning for 2 years but freeze up every time...",
        url="https://reddit.com/r/languagelearning/abc123",
        permalink="/r/languagelearning/comments/abc123/scared_to_speak/",
        created_utc=1702800000.0,
        score=42,
        num_comments=15,
    )

    print("Sample RedditPost:")
    print(f"  Full text: {sample_post.full_text[:60]}...")
    print(f"  Direct URL: {sample_post.direct_url}")
    print(f"  Message URL: {sample_post.message_url}")

    lead = Lead.from_post(
        sample_post,
        matched_triggers=["scared to speak", "in-laws", "freeze up"],
        language_detected="ja",
    )

    print("\nConverted Lead:")
    print(f"  Author: {lead.author}")
    print(f"  Triggers: {lead.matched_triggers}")
    print(f"  Language: {lead.language_detected}")

    print("\nCSV Row:")
    for key, value in lead.to_csv_row().items():
        print(f"  {key}: {value}")
