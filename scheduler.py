#!/usr/bin/env python3
"""
Background scheduler for Kaiwa Reddit Scout.

Run this script to continuously scan Reddit at a configurable interval.
The script runs in the background and logs all output.

Usage:
    # Run with default settings (every 60 minutes)
    python3 scheduler.py

    # Run every 30 minutes
    python3 scheduler.py --interval 30

    # Run with custom options
    python3 scheduler.py --interval 60 --limit 100 --sheets

    # Run in background (survives terminal close)
    nohup python3 scheduler.py --interval 60 --sheets > logs/scheduler.log 2>&1 &

To stop:
    # Find the process
    ps aux | grep scheduler.py

    # Kill it
    kill <PID>

    # Or use pkill
    pkill -f scheduler.py
"""

import argparse
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure we're in the right directory
SCRIPT_DIR = Path(__file__).parent.absolute()
os.chdir(SCRIPT_DIR)

# Create logs directory if it doesn't exist
LOGS_DIR = SCRIPT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Set up logging
LOG_FILE = LOGS_DIR / "scheduler.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Flag for graceful shutdown
running = True


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    running = False


def run_scout(limit: int, analyze: bool, sheets: bool, verbose: bool) -> bool:
    """
    Run the Kaiwa Reddit Scout main script.

    Returns True if successful, False otherwise.
    """
    cmd = [sys.executable, "-m", "src.main"]

    if analyze:
        cmd.append("--analyze")
    if sheets:
        cmd.append("--sheets")
    if verbose:
        cmd.append("-v")
    cmd.extend(["--limit", str(limit)])

    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )

        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                if line:
                    logger.info(f"[scout] {line}")

        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                if line:
                    logger.warning(f"[scout] {line}")

        if result.returncode == 0:
            logger.info("Scout completed successfully")
            return True
        else:
            logger.error(f"Scout exited with code {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Scout timed out after 30 minutes")
        return False
    except Exception as e:
        logger.error(f"Error running scout: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Background scheduler for Kaiwa Reddit Scout",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 scheduler.py                          # Run every 60 min (default)
    python3 scheduler.py --interval 30            # Run every 30 min
    python3 scheduler.py --interval 60 --sheets   # With Google Sheets export
    python3 scheduler.py --run-once               # Run once and exit

Background usage:
    nohup python3 scheduler.py --sheets > logs/scheduler.log 2>&1 &
        """
    )

    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=60,
        help="Interval between runs in minutes (default: 60)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=100,
        help="Max posts to fetch per run (default: 100)"
    )
    parser.add_argument(
        "--analyze", "-a",
        action="store_true",
        default=True,
        help="Enable AI analysis (default: True)"
    )
    parser.add_argument(
        "--no-analyze",
        action="store_true",
        help="Disable AI analysis"
    )
    parser.add_argument(
        "--sheets",
        action="store_true",
        help="Export to Google Sheets"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run once and exit (useful for testing)"
    )

    args = parser.parse_args()

    # Handle --no-analyze flag
    analyze = args.analyze and not args.no_analyze

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    interval_seconds = args.interval * 60

    logger.info("=" * 60)
    logger.info("Kaiwa Reddit Scout Scheduler Started")
    logger.info("=" * 60)
    logger.info(f"Interval: {args.interval} minutes")
    logger.info(f"Limit: {args.limit} posts")
    logger.info(f"AI Analysis: {'enabled' if analyze else 'disabled'}")
    logger.info(f"Google Sheets: {'enabled' if args.sheets else 'disabled'}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 60)

    if args.run_once:
        logger.info("Running once and exiting...")
        success = run_scout(args.limit, analyze, args.sheets, args.verbose)
        sys.exit(0 if success else 1)

    logger.info("Press Ctrl+C to stop")

    run_count = 0
    success_count = 0

    while running:
        run_count += 1
        logger.info(f"\n{'=' * 40}")
        logger.info(f"Run #{run_count} starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'=' * 40}")

        success = run_scout(args.limit, analyze, args.sheets, args.verbose)
        if success:
            success_count += 1

        logger.info(f"Stats: {success_count}/{run_count} successful runs")

        if not running:
            break

        next_run = datetime.now().timestamp() + interval_seconds
        next_run_str = datetime.fromtimestamp(next_run).strftime('%H:%M:%S')
        logger.info(f"Next run at {next_run_str} (sleeping for {args.interval} minutes)")

        # Sleep in small increments to allow for graceful shutdown
        sleep_end = time.time() + interval_seconds
        while running and time.time() < sleep_end:
            time.sleep(min(10, sleep_end - time.time()))

    logger.info("\n" + "=" * 60)
    logger.info("Scheduler stopped")
    logger.info(f"Total runs: {run_count}, Successful: {success_count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
