#!/usr/bin/env python3
"""
Kaiwa Action CLI - Streamlined workflow for posting comments

Usage:
    python action.py              # List pending leads
    python action.py --next       # Show next lead to action
    python action.py --sent ID    # Mark a lead as sent
    python action.py --open       # Open next lead in browser + copy comment
"""

import argparse
import csv
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

# Try to import pyperclip for clipboard, but make it optional
try:
    import pyperclip
    HAS_CLIPBOARD = True
except ImportError:
    HAS_CLIPBOARD = False


DATA_DIR = Path("data")
LEADS_FILE = DATA_DIR / "leads.csv"


def load_leads():
    """Load leads from CSV."""
    if not LEADS_FILE.exists():
        return []

    with open(LEADS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_leads(leads):
    """Save leads back to CSV."""
    if not leads:
        return

    fieldnames = leads[0].keys()
    with open(LEADS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)


def get_pending_leads(leads):
    """Get leads that are comment-worthy but not yet sent."""
    pending = []
    for lead in leads:
        # Check if comment-worthy and has a draft
        comment_worthy = lead.get("comment_worthy", "").lower() == "yes"
        has_draft = bool(lead.get("public_draft", "").strip())
        sent = lead.get("sent", "").lower() in ("yes", "true", "1")

        if comment_worthy and has_draft and not sent:
            pending.append(lead)

    return pending


def extract_post_id(post_url):
    """Extract Reddit post ID from URL."""
    # URL format: https://reddit.com/r/sub/comments/POST_ID/...
    parts = post_url.split("/comments/")
    if len(parts) > 1:
        return parts[1].split("/")[0]
    return None


def print_lead(lead, index=None):
    """Print a lead in a readable format."""
    prefix = f"[{index}] " if index is not None else ""

    print(f"\n{prefix}r/{lead.get('subreddit', 'unknown')}")
    print(f"    Title: {lead.get('title', '')[:60]}...")
    print(f"    Score: {lead.get('signal_score', '?')}/10 ({lead.get('category', 'unknown')})")
    print(f"    URL:   {lead.get('post_url', '')}")

    draft = lead.get("public_draft", "")
    if draft:
        # Show first 100 chars of draft
        preview = draft[:100].replace("\n", " ")
        print(f"    Draft: {preview}...")


def cmd_list(args):
    """List all pending leads."""
    leads = load_leads()
    pending = get_pending_leads(leads)

    if not pending:
        print("No pending leads to action.")
        print("\nRun the scout to find new leads:")
        print("  python -m src.main --analyze --sheets")
        return

    print(f"\n{'='*60}")
    print(f"PENDING LEADS ({len(pending)} to action)")
    print("="*60)

    for i, lead in enumerate(pending, 1):
        print_lead(lead, i)

    print(f"\n{'='*60}")
    print("Quick actions:")
    print("  python action.py --next       # Show next lead with full draft")
    print("  python action.py --open       # Open in browser + copy comment")
    print("  python action.py --sent ID    # Mark as sent (e.g. --sent 1prpfyi)")


def cmd_next(args):
    """Show the next lead to action with full details."""
    leads = load_leads()
    pending = get_pending_leads(leads)

    if not pending:
        print("No pending leads to action.")
        return

    lead = pending[0]
    post_id = extract_post_id(lead.get("post_url", ""))

    print(f"\n{'='*60}")
    print("NEXT LEAD TO ACTION")
    print("="*60)
    print(f"\nSubreddit: r/{lead.get('subreddit', 'unknown')}")
    print(f"Title:     {lead.get('title', '')}")
    print(f"Score:     {lead.get('signal_score', '?')}/10 - {lead.get('category', '')}")
    print(f"Post ID:   {post_id}")
    print(f"\nPost URL:  {lead.get('post_url', '')}")
    print(f"DM URL:    {lead.get('message_url', '')}")

    print(f"\n{'-'*60}")
    print("DRAFT COMMENT (copy this):")
    print("-"*60)
    draft = lead.get("public_draft", "")
    print(draft)
    print("-"*60)

    print(f"\nWhen done, mark as sent:")
    print(f"  python action.py --sent {post_id}")


def cmd_open(args):
    """Open the next lead in browser and copy comment to clipboard."""
    leads = load_leads()
    pending = get_pending_leads(leads)

    if not pending:
        print("No pending leads to action.")
        return

    lead = pending[0]
    post_url = lead.get("post_url", "")
    draft = lead.get("public_draft", "")
    post_id = extract_post_id(post_url)

    # Copy draft to clipboard
    if HAS_CLIPBOARD and draft:
        pyperclip.copy(draft)
        print("Draft comment copied to clipboard!")
    elif draft:
        print("Install pyperclip for auto-copy: pip install pyperclip")
        print("\nDraft comment:")
        print("-"*40)
        print(draft)
        print("-"*40)

    # Open in browser
    if post_url:
        print(f"\nOpening: {post_url}")
        webbrowser.open(post_url)

    print(f"\nWhen done, run: python action.py --sent {post_id}")


def cmd_sent(args):
    """Mark a lead as sent."""
    if not args.post_id:
        print("Error: Please provide a post ID")
        print("Usage: python action.py --sent POST_ID")
        return

    leads = load_leads()
    found = False

    for lead in leads:
        post_url = lead.get("post_url", "")
        if args.post_id in post_url:
            lead["sent"] = "yes"
            lead["sent_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            found = True
            print(f"Marked as sent: {lead.get('title', '')[:50]}...")
            break

    if found:
        save_leads(leads)

        # Show remaining count
        pending = get_pending_leads(leads)
        print(f"\n{len(pending)} leads remaining")
    else:
        print(f"Lead not found: {args.post_id}")
        print("Use the post ID from the URL, e.g.: 1prpfyi")


def cmd_stats(args):
    """Show action statistics."""
    leads = load_leads()

    total = len(leads)
    comment_worthy = sum(1 for l in leads if l.get("comment_worthy", "").lower() == "yes")
    sent = sum(1 for l in leads if l.get("sent", "").lower() in ("yes", "true", "1"))
    pending = len(get_pending_leads(leads))

    print(f"\n{'='*60}")
    print("ACTION STATISTICS")
    print("="*60)
    print(f"Total leads:      {total}")
    print(f"Comment-worthy:   {comment_worthy}")
    print(f"Sent:             {sent}")
    print(f"Pending:          {pending}")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Kaiwa Action CLI - Streamlined workflow for posting comments"
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all pending leads (default action)",
    )
    parser.add_argument(
        "--next", "-n",
        action="store_true",
        help="Show next lead with full draft",
    )
    parser.add_argument(
        "--open", "-o",
        action="store_true",
        help="Open next lead in browser + copy comment",
    )
    parser.add_argument(
        "--sent", "-s",
        dest="post_id",
        metavar="ID",
        help="Mark a lead as sent by post ID",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show action statistics",
    )

    args = parser.parse_args()

    # Determine which command to run
    if args.post_id:
        cmd_sent(args)
    elif args.next:
        cmd_next(args)
    elif args.open:
        cmd_open(args)
    elif args.stats:
        cmd_stats(args)
    else:
        # Default: list pending leads
        cmd_list(args)


if __name__ == "__main__":
    main()
