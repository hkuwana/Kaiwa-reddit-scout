"""
Google Sheets client for storing leads.
"""

import json
import logging
from datetime import datetime
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from src.config.settings import sheets_config
from src.storage.models import Lead

logger = logging.getLogger(__name__)

# Scopes required for Google Sheets API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Sheet headers
SHEET_HEADERS = [
    "Timestamp",
    "Subreddit",
    "Author",
    "Title",
    "Post URL",
    "DM URL",
    "Matched Keywords",
    "Language",
    "Signal Score",
    "Signal Type",
    "Category",
    "Public Draft",
    "DM Draft",
    "Status",
]


class SheetsClient:
    """Client for writing leads to Google Sheets."""

    def __init__(self, sheet_name: Optional[str] = None):
        """
        Initialize Sheets client.

        Args:
            sheet_name: Name of the spreadsheet to use
        """
        self.sheet_name = sheet_name or sheets_config.sheet_name
        self._client = None
        self._sheet = None

    def is_configured(self) -> bool:
        """Check if Sheets is configured."""
        return sheets_config.is_valid()

    def _get_client(self):
        """Lazy initialization of gspread client."""
        if self._client is None:
            if sheets_config.has_inline_json():
                # Parse inline JSON credentials from env var
                creds_info = json.loads(sheets_config.credentials_json)
                credentials = Credentials.from_service_account_info(
                    creds_info, scopes=SCOPES
                )
            else:
                # Load from file
                creds_path = sheets_config.get_credentials_path()
                if not creds_path.exists():
                    raise FileNotFoundError(
                        f"Google credentials file not found: {creds_path}"
                    )
                credentials = Credentials.from_service_account_file(
                    str(creds_path), scopes=SCOPES
                )

            self._client = gspread.authorize(credentials)

        return self._client

    def _get_or_create_sheet(self):
        """Get existing sheet or create new one."""
        if self._sheet is not None:
            return self._sheet

        client = self._get_client()

        try:
            # Try to open existing spreadsheet
            self._sheet = client.open(self.sheet_name).sheet1
            logger.info(f"Opened existing sheet: {self.sheet_name}")
        except gspread.SpreadsheetNotFound:
            # Create new spreadsheet
            if sheets_config.folder_id:
                # Create in specific folder
                spreadsheet = client.create(self.sheet_name, folder_id=sheets_config.folder_id)
                logger.info(f"Created new sheet in folder: {self.sheet_name}")
            else:
                spreadsheet = client.create(self.sheet_name)
                logger.info(f"Created new sheet: {self.sheet_name}")

            self._sheet = spreadsheet.sheet1

            # Add headers
            self._sheet.append_row(SHEET_HEADERS)

            # Format header row (bold)
            self._sheet.format("A1:N1", {"textFormat": {"bold": True}})

            # Auto-resize columns
            self._sheet.columns_auto_resize(0, len(SHEET_HEADERS) - 1)

        return self._sheet

    def _lead_to_row(self, lead: Lead) -> list:
        """Convert a Lead to a sheet row."""
        return [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            lead.subreddit,
            lead.author,
            lead.title[:100],  # Truncate for readability
            lead.post_url,
            lead.message_url,
            ", ".join(lead.matched_triggers[:5]),  # Limit triggers
            lead.language_detected or "",
            lead.signal_score or "",
            lead.signal_type or "",
            lead.category or "",
            lead.public_draft or "",
            lead.dm_draft or "",
            lead.status,
        ]

    def get_existing_post_ids(self) -> set[str]:
        """Get set of post IDs already in the sheet."""
        if not self.is_configured():
            return set()

        try:
            sheet = self._get_or_create_sheet()
            # Get all Post URLs (column E)
            post_urls = sheet.col_values(5)  # 1-indexed

            post_ids = set()
            for url in post_urls[1:]:  # Skip header
                # Extract post ID from URL
                # URL format: https://reddit.com/r/sub/comments/POST_ID/...
                parts = url.split("/comments/")
                if len(parts) > 1:
                    post_id = parts[1].split("/")[0]
                    post_ids.add(post_id)

            return post_ids

        except Exception as e:
            logger.warning(f"Error getting existing posts from sheet: {e}")
            return set()

    def append_lead(self, lead: Lead) -> bool:
        """
        Append a single lead to the sheet.

        Args:
            lead: Lead to append

        Returns:
            True if appended, False if duplicate or error
        """
        if not self.is_configured():
            logger.warning("Google Sheets not configured")
            return False

        try:
            # Check for duplicates
            existing_ids = self.get_existing_post_ids()
            if lead.post_id in existing_ids:
                logger.debug(f"Skipping duplicate in sheet: {lead.post_id}")
                return False

            sheet = self._get_or_create_sheet()
            row = self._lead_to_row(lead)
            sheet.append_row(row, value_input_option="USER_ENTERED")

            logger.info(f"Added lead to sheet: u/{lead.author} ({lead.post_id})")
            return True

        except Exception as e:
            logger.error(f"Error appending to sheet: {e}")
            return False

    def append_leads(self, leads: list[Lead]) -> dict:
        """
        Append multiple leads to the sheet.

        Args:
            leads: List of leads to append

        Returns:
            Stats dict with saved/skipped counts
        """
        if not self.is_configured():
            logger.warning("Google Sheets not configured - skipping sheet output")
            return {"saved": 0, "skipped": len(leads)}

        if not leads:
            return {"saved": 0, "skipped": 0}

        try:
            # Get existing IDs once
            existing_ids = self.get_existing_post_ids()

            # Prepare rows to append
            rows = []
            saved = 0
            skipped = 0

            for lead in leads:
                if lead.post_id in existing_ids:
                    skipped += 1
                    continue

                rows.append(self._lead_to_row(lead))
                existing_ids.add(lead.post_id)  # Track for this batch
                saved += 1

            # Batch append
            if rows:
                sheet = self._get_or_create_sheet()
                sheet.append_rows(rows, value_input_option="USER_ENTERED")

            logger.info(f"Added {saved} leads to sheet, skipped {skipped} duplicates")
            return {"saved": saved, "skipped": skipped}

        except Exception as e:
            logger.error(f"Error batch appending to sheet: {e}")
            return {"saved": 0, "skipped": len(leads)}

    def get_sheet_url(self) -> Optional[str]:
        """Get the URL of the spreadsheet."""
        if not self.is_configured():
            return None

        try:
            client = self._get_client()
            spreadsheet = client.open(self.sheet_name)
            # Construct URL from spreadsheet ID (more reliable)
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
        except Exception as e:
            logger.error(f"Error getting sheet URL: {e}")
            return None

    def list_available_sheets(self) -> list[dict]:
        """List all spreadsheets accessible to the service account."""
        if not self.is_configured():
            return []

        try:
            client = self._get_client()
            sheets = client.openall()
            return [
                {
                    "name": s.title,
                    "id": s.id,
                    "url": f"https://docs.google.com/spreadsheets/d/{s.id}",
                }
                for s in sheets
            ]
        except Exception as e:
            logger.error(f"Error listing sheets: {e}")
            return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Testing Sheets Client")
    print("=" * 50)

    client = SheetsClient()
    print(f"Configured: {client.is_configured()}")

    if client.is_configured():
        url = client.get_sheet_url()
        print(f"Sheet URL: {url}")
    else:
        print("\nTo configure Google Sheets:")
        print("1. Create a service account at console.cloud.google.com")
        print("2. Enable Google Sheets API")
        print("3. Download JSON credentials as 'google_creds.json'")
        print("4. Place in project root directory")
