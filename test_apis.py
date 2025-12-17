#!/usr/bin/env python3
"""
API Test Script for Kaiwa Reddit Scout

Run this script to verify all your API keys are working:
    python test_apis.py

Or test individual APIs:
    python test_apis.py --gemini
    python test_apis.py --reddit
    python test_apis.py --resend
"""

import argparse
import sys
from datetime import datetime


def test_config():
    """Test that configuration is loaded correctly."""
    print("\n" + "=" * 60)
    print("1. CONFIGURATION CHECK")
    print("=" * 60)

    from src.config.settings import reddit_config, gemini_config, app_config

    results = {
        "Reddit API": reddit_config.is_valid(),
        "Gemini API": gemini_config.is_valid(),
    }

    print(f"Reddit API configured: {results['Reddit API']}")
    if results['Reddit API']:
        print(f"  - Client ID: ***{reddit_config.client_id[-4:] if len(reddit_config.client_id) > 4 else '(short)'}")
        print(f"  - Username: {reddit_config.username}")

    print(f"Gemini API configured: {results['Gemini API']}")
    if results['Gemini API']:
        print(f"  - Model: {gemini_config.model}")
        print(f"  - Signal threshold: {gemini_config.signal_threshold}")

    print(f"Data directory: {app_config.data_dir}")

    return all(results.values())


def test_gemini():
    """Test Gemini API connection."""
    print("\n" + "=" * 60)
    print("2. GEMINI API TEST")
    print("=" * 60)

    from src.analyzer.gemini_client import GeminiClient

    client = GeminiClient()

    if not client.is_configured():
        print("SKIP: Gemini API key not configured")
        return False

    print("Testing text generation...")
    response = client.generate("Say 'Hello, I am working!' in exactly those words.")

    if response:
        print(f"SUCCESS: {response[:100]}...")

        # Test JSON generation
        print("\nTesting JSON generation...")
        json_response = client.generate_json('Return a JSON object with {"status": "ok", "test": true}')
        if json_response:
            print(f"JSON SUCCESS: {json_response[:100]}")
            return True
        else:
            print("FAILED: JSON generation failed")
            return False
    else:
        print("FAILED: No response from Gemini API")
        print("Check that your GEMINI_API_KEY is valid at https://aistudio.google.com/apikey")
        return False


def test_reddit():
    """Test Reddit API connection."""
    print("\n" + "=" * 60)
    print("3. REDDIT API TEST")
    print("=" * 60)

    from src.scraper.reddit_client import get_reddit_client

    try:
        client = get_reddit_client(use_mock=False)
        print(f"Client type: {type(client).__name__}")

        if type(client).__name__ == "MockRedditClient":
            print("SKIP: Using mock client (credentials not configured)")
            return False

        print("Fetching 1 post from r/languagelearning...")
        posts = list(client.get_new_posts(["languagelearning"], limit=1))

        if posts:
            post = posts[0]
            print(f"SUCCESS: Fetched post from r/{post.subreddit}")
            print(f"  Title: {post.title[:50]}...")
            print(f"  Author: u/{post.author}")
            return True
        else:
            print("WARNING: No posts fetched (subreddit might be empty)")
            return True  # API works, just no posts

    except Exception as e:
        print(f"FAILED: {e}")
        print("\nCheck your Reddit credentials at https://www.reddit.com/prefs/apps")
        return False


def test_resend():
    """Test Resend email API."""
    print("\n" + "=" * 60)
    print("4. RESEND EMAIL API TEST")
    print("=" * 60)

    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("RESEND_API_KEY", "")
    email_to = os.getenv("EMAIL_TO", "")
    email_from = os.getenv("EMAIL_FROM", "onboarding@resend.dev")

    if not api_key or api_key == "re_your_api_key_here":
        print("SKIP: RESEND_API_KEY not configured")
        return False

    if not email_to or email_to == "your_email@example.com":
        print("SKIP: EMAIL_TO not configured")
        return False

    try:
        import resend

        resend.api_key = api_key

        print(f"Sending test email to {email_to}...")

        email = resend.Emails.send({
            "from": email_from,
            "to": email_to,
            "subject": "Kaiwa Reddit Scout - Test Email",
            "html": f"""
            <h2>Test Email from Kaiwa Reddit Scout</h2>
            <p>Your Resend API is working correctly!</p>
            <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            """
        })

        print(f"SUCCESS: Email sent!")
        print(f"  Email ID: {email.get('id', 'unknown')}")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        print("\nCheck your Resend API key at https://resend.com/api-keys")
        return False


def test_sheets():
    """Test Google Sheets connection."""
    print("\n" + "=" * 60)
    print("5. GOOGLE SHEETS API TEST")
    print("=" * 60)

    from src.config.settings import sheets_config

    if not sheets_config.is_valid():
        print("SKIP: Google Sheets credentials not configured")
        print("  Add google_creds.json to project root to enable")
        return False

    try:
        from src.output import SheetsClient

        print("Connecting to Google Sheets...")
        client = SheetsClient()

        # List all accessible sheets
        print("\nSheets accessible to service account:")
        sheets = client.list_available_sheets()
        if sheets:
            for s in sheets:
                marker = " <-- TARGET" if s["name"] == sheets_config.sheet_name else ""
                print(f"  - {s['name']}{marker}")
                print(f"    {s['url']}")
        else:
            print("  (none found - share your sheet with the service account email)")

        print(f"\nLooking for: '{sheets_config.sheet_name}'")
        url = client.get_sheet_url()
        if url:
            print(f"SUCCESS: Found sheet!")
            print(f"  URL: {url}")
        else:
            print("NOT FOUND: Sheet not accessible")
            print("  Make sure to share your Google Sheet with the service account email")

        return True

    except Exception as e:
        print(f"FAILED: {e}")
        print("\nCheck your Google credentials at https://console.cloud.google.com/")
        return False


def test_full_pipeline():
    """Test the full pipeline with mock data."""
    print("\n" + "=" * 60)
    print("6. FULL PIPELINE TEST (Mock Data)")
    print("=" * 60)

    try:
        from src.main import run_scout

        print("Running scout with mock data...")
        result = run_scout(limit=5, use_mock=True, analyze=True, verbose=False)

        print(f"SUCCESS: Pipeline completed!")
        print(f"  Posts fetched: {result['posts_fetched']}")
        print(f"  Leads found: {result['leads_found']}")
        print(f"  High-signal leads: {result['high_signal_leads']}")
        print(f"  Leads saved: {result['leads_saved']}")
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Kaiwa Reddit Scout APIs")
    parser.add_argument("--gemini", action="store_true", help="Test only Gemini API")
    parser.add_argument("--reddit", action="store_true", help="Test only Reddit API")
    parser.add_argument("--resend", action="store_true", help="Test only Resend API")
    parser.add_argument("--sheets", action="store_true", help="Test only Google Sheets")
    parser.add_argument("--pipeline", action="store_true", help="Test full pipeline")
    args = parser.parse_args()

    print("=" * 60)
    print("KAIWA REDDIT SCOUT - API TEST SUITE")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Determine which tests to run
    run_all = not any([args.gemini, args.reddit, args.resend, args.sheets, args.pipeline])

    results = {}

    # Always check config first
    if run_all or args.gemini or args.reddit:
        results["Config"] = test_config()

    if run_all or args.gemini:
        results["Gemini"] = test_gemini()

    if run_all or args.reddit:
        results["Reddit"] = test_reddit()

    if run_all or args.resend:
        results["Resend"] = test_resend()

    if run_all or args.sheets:
        results["Sheets"] = test_sheets()

    if run_all or args.pipeline:
        results["Pipeline"] = test_full_pipeline()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results.items():
        status = "PASS" if passed else "FAIL" if passed is False else "SKIP"
        emoji = "✓" if passed else "✗" if passed is False else "-"
        print(f"  {emoji} {name}: {status}")

    all_passed = all(v for v in results.values() if v is not None)
    print("=" * 60)

    if all_passed:
        print("All tests passed! Your setup is ready.")
    else:
        print("Some tests failed. Check the output above for details.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
