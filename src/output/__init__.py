"""
Output module for exporting leads.

Components:
- SheetsClient: Export leads to Google Sheets
"""

from src.output.sheets_client import SheetsClient

__all__ = ["SheetsClient"]
