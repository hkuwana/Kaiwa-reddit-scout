"""
CSV storage for leads.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config.settings import app_config
from src.storage.models import Lead

logger = logging.getLogger(__name__)

# CSV column order (Phase 1 + Phase 2 columns)
CSV_COLUMNS = [
    "scraped_at",
    "created_at",
    "subreddit",
    "author",
    "title",
    "post_url",
    "message_url",
    "matched_triggers",
    "language",
    "score",
    "comments",
    "status",
    # Phase 2: AI analysis columns
    "signal_score",
    "signal_type",
    "category",
    "comment_worthy",
    "comment_worthy_reason",
    "public_draft",
    "dm_draft",
]


class CSVStorage:
    """Manage lead storage in CSV files."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize CSV storage.

        Args:
            data_dir: Directory for CSV files (default: data/)
        """
        self.data_dir = data_dir or app_config.data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.leads_file = self.data_dir / "leads.csv"

    def _ensure_file_exists(self):
        """Create CSV file with headers if it doesn't exist."""
        if not self.leads_file.exists():
            with open(self.leads_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
            logger.info(f"Created new leads file: {self.leads_file}")

    def get_existing_post_ids(self) -> set[str]:
        """Get set of post IDs already in storage (for deduplication)."""
        if not self.leads_file.exists():
            return set()

        try:
            df = pd.read_csv(self.leads_file)
            # Extract post IDs from URLs
            post_ids = set()
            for url in df["post_url"]:
                # URL format: https://reddit.com/r/sub/comments/POST_ID/...
                parts = url.split("/comments/")
                if len(parts) > 1:
                    post_id = parts[1].split("/")[0]
                    post_ids.add(post_id)
            return post_ids
        except Exception as e:
            logger.warning(f"Error reading existing posts: {e}")
            return set()

    def save_lead(self, lead: Lead) -> bool:
        """
        Save a single lead to CSV.

        Args:
            lead: Lead object to save

        Returns:
            True if saved, False if duplicate
        """
        self._ensure_file_exists()

        # Check for duplicate
        existing_ids = self.get_existing_post_ids()
        if lead.post_id in existing_ids:
            logger.debug(f"Skipping duplicate: {lead.post_id}")
            return False

        # Append to CSV
        with open(self.leads_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writerow(lead.to_csv_row())

        logger.info(f"Saved lead: u/{lead.author} ({lead.post_id})")
        return True

    def save_leads(self, leads: list[Lead]) -> dict:
        """
        Save multiple leads to CSV.

        Args:
            leads: List of Lead objects

        Returns:
            Stats dict with saved/skipped counts
        """
        self._ensure_file_exists()
        existing_ids = self.get_existing_post_ids()

        saved = 0
        skipped = 0

        with open(self.leads_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)

            for lead in leads:
                if lead.post_id in existing_ids:
                    skipped += 1
                    continue

                writer.writerow(lead.to_csv_row())
                existing_ids.add(lead.post_id)  # Track for this batch
                saved += 1

        logger.info(f"Saved {saved} leads, skipped {skipped} duplicates")
        return {"saved": saved, "skipped": skipped}

    def get_leads(
        self,
        status: Optional[str] = None,
        language: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Read leads from CSV with optional filtering.

        Args:
            status: Filter by status (new, contacted, etc.)
            language: Filter by language code
            limit: Max rows to return

        Returns:
            DataFrame of leads
        """
        if not self.leads_file.exists():
            return pd.DataFrame(columns=CSV_COLUMNS)

        df = pd.read_csv(self.leads_file)

        if status:
            df = df[df["status"] == status]
        if language:
            df = df[df["language"] == language]
        if limit:
            df = df.head(limit)

        return df

    def get_stats(self) -> dict:
        """Get storage statistics."""
        if not self.leads_file.exists():
            return {"total": 0, "by_status": {}, "by_language": {}}

        df = pd.read_csv(self.leads_file)

        return {
            "total": len(df),
            "by_status": df["status"].value_counts().to_dict(),
            "by_language": df["language"].value_counts().to_dict(),
            "by_subreddit": df["subreddit"].value_counts().to_dict(),
        }

    def update_status(self, post_id: str, new_status: str) -> bool:
        """
        Update the status of a lead.

        Args:
            post_id: Reddit post ID
            new_status: New status value

        Returns:
            True if updated, False if not found
        """
        if not self.leads_file.exists():
            return False

        df = pd.read_csv(self.leads_file)

        # Find by post_id in URL
        mask = df["post_url"].str.contains(f"/comments/{post_id}/")
        if not mask.any():
            return False

        df.loc[mask, "status"] = new_status
        df.to_csv(self.leads_file, index=False)
        return True

    def export_for_action(self, output_file: Optional[Path] = None) -> Path:
        """
        Export new leads to a clean CSV for daily action.

        Args:
            output_file: Optional custom output path

        Returns:
            Path to exported file
        """
        if output_file is None:
            date_str = datetime.now().strftime("%Y%m%d")
            output_file = self.data_dir / f"leads_action_{date_str}.csv"

        df = self.get_leads(status="new")

        # Select action-relevant columns
        action_cols = [
            "subreddit",
            "author",
            "title",
            "post_url",
            "message_url",
            "matched_triggers",
            "language",
        ]
        df[action_cols].to_csv(output_file, index=False)

        logger.info(f"Exported {len(df)} leads to {output_file}")
        return output_file


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    from src.storage.models import Lead, RedditPost

    print("Testing CSV Storage")
    print("=" * 50)

    # Create test storage
    storage = CSVStorage()

    # Create sample leads
    sample_leads = [
        Lead.from_post(
            RedditPost(
                id="csv_test1",
                subreddit="languagelearning",
                author="test_user1",
                title="Scared to speak with in-laws",
                selftext="I freeze up when speaking Japanese...",
                url="https://reddit.com/r/languagelearning/csv_test1",
                permalink="/r/languagelearning/comments/csv_test1/test/",
                created_utc=1702800000.0,
                score=42,
                num_comments=15,
            ),
            matched_triggers=["scared to speak", "in-laws", "freeze up"],
            language_detected="ja",
        ),
        Lead.from_post(
            RedditPost(
                id="csv_test2",
                subreddit="learnspanish",
                author="test_user2",
                title="Moving to Spain, frustrated I can't speak",
                selftext="Been learning for a year but still can't converse...",
                url="https://reddit.com/r/learnspanish/csv_test2",
                permalink="/r/learnspanish/comments/csv_test2/test/",
                created_utc=1702790000.0,
                score=28,
                num_comments=12,
            ),
            matched_triggers=["moving to", "frustrated", "can't speak"],
            language_detected="es",
        ),
    ]

    # Save leads
    print("\nSaving leads:")
    result = storage.save_leads(sample_leads)
    print(f"  Saved: {result['saved']}, Skipped: {result['skipped']}")

    # Try saving duplicates
    print("\nSaving same leads again (should skip):")
    result = storage.save_leads(sample_leads)
    print(f"  Saved: {result['saved']}, Skipped: {result['skipped']}")

    # Get stats
    print("\nStorage stats:")
    stats = storage.get_stats()
    print(f"  Total leads: {stats['total']}")
    print(f"  By status: {stats['by_status']}")
    print(f"  By language: {stats['by_language']}")

    # Read leads
    print("\nAll leads:")
    df = storage.get_leads()
    print(df.to_string(index=False))

    print(f"\nCSV file location: {storage.leads_file}")
