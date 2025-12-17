"""
Kaiwa Reddit Scout - Main Entry Point

Phase 1: Scrape Reddit posts, filter by keywords, save to CSV.
Phase 2: Analyze leads with Gemini AI, score signals, generate responses.
Phase 3: Export to Google Sheets with timestamps.
"""

import argparse
import logging
import sys
from datetime import datetime

from src.config.settings import app_config, gemini_config, sheets_config, print_config_status
from src.config.languages import get_all_subreddits, LANGUAGES
from src.scraper.reddit_client import get_reddit_client
from src.scraper.keyword_filter import KeywordFilter
from src.storage.csv_storage import CSVStorage


def setup_logging(level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_scout(
    subreddits: list[str] | None = None,
    limit: int = 100,
    use_mock: bool = False,
    verbose: bool = False,
    analyze: bool = False,
    use_sheets: bool = False,
) -> dict:
    """
    Run the Reddit scout pipeline.

    Args:
        subreddits: List of subreddits to monitor (default: all language learning subs)
        limit: Maximum posts to fetch
        use_mock: Use mock client for testing
        verbose: Print detailed output
        analyze: Run AI analysis with Gemini (Phase 2)
        use_sheets: Export to Google Sheets (Phase 3)

    Returns:
        Dict with run statistics
    """
    logger = logging.getLogger(__name__)

    # Use all subreddits if not specified
    if not subreddits:
        subreddits = get_all_subreddits()

    logger.info(f"Starting Kaiwa Reddit Scout")
    logger.info(f"Monitoring {len(subreddits)} subreddits, limit={limit}")

    # Initialize components
    client = get_reddit_client(use_mock=use_mock)
    keyword_filter = KeywordFilter()
    storage = CSVStorage()

    # Fetch posts
    logger.info("Fetching posts from Reddit...")
    posts = list(client.get_new_posts(subreddits, limit=limit))
    logger.info(f"Fetched {len(posts)} posts")

    # Filter posts
    logger.info("Filtering posts by keywords...")
    leads = list(keyword_filter.filter_posts(iter(posts)))
    logger.info(f"Found {len(leads)} potential leads")

    if verbose:
        keyword_filter.print_stats()

    # Phase 2: AI Analysis with Gemini
    high_signal_count = 0
    if analyze and leads:
        if gemini_config.is_valid():
            logger.info("Running AI analysis with Gemini...")

            # Lazy import to avoid loading Gemini when not needed
            from src.analyzer import SignalScorer, ResponseGenerator

            # Score leads
            scorer = SignalScorer()
            leads = scorer.score_leads(leads)

            # Filter high-signal leads for response generation
            high_signal_leads = scorer.filter_high_signal(leads)
            high_signal_count = len(high_signal_leads)
            logger.info(f"Found {high_signal_count} high-signal leads (score >= {gemini_config.signal_threshold})")

            # Generate responses only for high-signal leads
            if high_signal_leads:
                logger.info("Generating response drafts for high-signal leads...")
                generator = ResponseGenerator()
                generator.generate_responses_batch(high_signal_leads)
        else:
            logger.warning("Gemini API not configured - skipping AI analysis")
            logger.warning("Set GEMINI_API_KEY in .env to enable analysis")

    # Save to CSV
    if leads:
        logger.info("Saving leads to CSV...")
        save_result = storage.save_leads(leads)
        logger.info(f"Saved {save_result['saved']} new leads, skipped {save_result['skipped']} duplicates")
    else:
        save_result = {"saved": 0, "skipped": 0}
        logger.info("No leads to save")

    # Phase 3: Export to Google Sheets
    sheets_result = {"saved": 0, "skipped": 0}
    sheet_url = None
    if use_sheets and leads:
        if sheets_config.is_valid():
            logger.info("Exporting to Google Sheets...")
            from src.output import SheetsClient
            sheets_client = SheetsClient()
            sheets_result = sheets_client.append_leads(leads)
            sheet_url = sheets_client.get_sheet_url()
            logger.info(f"Added {sheets_result['saved']} leads to sheet, skipped {sheets_result['skipped']} duplicates")
        else:
            logger.warning("Google Sheets not configured - skipping sheet export")
            logger.warning("Add google_creds.json to project root to enable Sheets")

    # Print summary
    print("\n" + "=" * 60)
    print("SCOUT RUN COMPLETE")
    print("=" * 60)
    print(f"  Time:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Subreddits:  {len(subreddits)}")
    print(f"  Posts found: {len(posts)}")
    print(f"  Leads found: {len(leads)}")
    if analyze:
        print(f"  High-signal: {high_signal_count}")
    print(f"  New saved:   {save_result['saved']}")
    print(f"  Duplicates:  {save_result['skipped']}")
    print(f"  CSV file:    {storage.leads_file}")
    if use_sheets and sheet_url:
        print(f"  Sheet:       {sheet_url}")
        print(f"  Sheet saved: {sheets_result['saved']}")
    print("=" * 60)

    # Show new leads
    if leads and verbose:
        print("\nNew Leads:")
        print("-" * 60)
        for lead in leads:
            print(f"\n  [{lead.subreddit}] u/{lead.author}")
            print(f"  Title: {lead.title[:60]}...")
            print(f"  Triggers: {', '.join(lead.matched_triggers[:3])}")
            print(f"  Language: {lead.language_detected or 'unknown'}")
            if analyze and lead.signal_score:
                print(f"  Signal: {lead.signal_score}/10 ({lead.signal_type}) - {lead.category}")
            print(f"  Link: {lead.post_url}")
            print(f"  DM: {lead.message_url}")

    return {
        "posts_fetched": len(posts),
        "leads_found": len(leads),
        "high_signal_leads": high_signal_count,
        "leads_saved": save_result["saved"],
        "leads_skipped": save_result["skipped"],
        "filter_stats": keyword_filter.get_stats(),
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Kaiwa Reddit Scout - Find language learning leads on Reddit"
    )

    parser.add_argument(
        "--subreddits",
        "-s",
        type=str,
        help="Comma-separated list of subreddits (default: all language learning subs)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=100,
        help="Maximum posts to fetch (default: 100)",
    )
    parser.add_argument(
        "--mock",
        "-m",
        action="store_true",
        help="Use mock data (for testing without Reddit API)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--analyze",
        "-a",
        action="store_true",
        help="Run AI analysis with Gemini (Phase 2)",
    )
    parser.add_argument(
        "--sheets",
        action="store_true",
        help="Export to Google Sheets (Phase 3)",
    )
    parser.add_argument(
        "--config",
        "-c",
        action="store_true",
        help="Show configuration status and exit",
    )
    parser.add_argument(
        "--languages",
        action="store_true",
        help="List supported languages and exit",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(app_config.log_level)

    # Handle info commands
    if args.config:
        print_config_status()
        return

    if args.languages:
        print("\nSupported Languages:")
        print("-" * 40)
        for code, lang in LANGUAGES.items():
            print(f"  [{code}] {lang.name}")
            print(f"       Subreddits: {', '.join(lang.subreddits)}")
        return

    # Parse subreddits
    subreddits = None
    if args.subreddits:
        subreddits = [s.strip() for s in args.subreddits.split(",")]

    # Run the scout
    try:
        run_scout(
            subreddits=subreddits,
            limit=args.limit,
            use_mock=args.mock,
            verbose=args.verbose,
            analyze=args.analyze,
            use_sheets=args.sheets,
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error: {e}")
        if args.verbose:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
