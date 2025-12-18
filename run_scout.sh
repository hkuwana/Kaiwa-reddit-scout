#!/bin/bash
# Kaiwa Reddit Scout - Background Runner
# Usage:
#   ./run_scout.sh          - Run once
#   ./run_scout.sh loop     - Run continuously (every hour)
#   ./run_scout.sh bg       - Run continuously in background

cd "$(dirname "$0")"

# Configuration
INTERVAL_SECONDS=3600  # 1 hour between runs
LIMIT=100              # Posts per run
LOG_FILE="logs/scout.log"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

run_once() {
    echo "=========================================="
    echo "Starting Kaiwa Reddit Scout - $(date)"
    echo "=========================================="

    # Try with Google Sheets first, fall back to CSV-only if it fails
    python3 -m src.main --analyze --sheets --limit $LIMIT 2>&1 || \
    python3 -m src.main --analyze --limit $LIMIT 2>&1

    echo ""
    echo "Completed at $(date)"
    echo "CSV saved to: data/leads.csv"
    echo "=========================================="
}

run_loop() {
    echo "Starting continuous mode (Ctrl+C to stop)"
    echo "Interval: $INTERVAL_SECONDS seconds ($((INTERVAL_SECONDS / 60)) minutes)"
    echo ""

    while true; do
        run_once
        echo ""
        echo "Sleeping for $((INTERVAL_SECONDS / 60)) minutes..."
        echo "Next run at: $(date -d "+$INTERVAL_SECONDS seconds" 2>/dev/null || date -v+${INTERVAL_SECONDS}S)"
        echo ""
        sleep $INTERVAL_SECONDS
    done
}

case "${1:-once}" in
    loop)
        run_loop
        ;;
    bg|background)
        echo "Starting in background mode..."
        echo "Logs: $LOG_FILE"
        echo "To stop: pkill -f 'run_scout.sh loop'"
        nohup "$0" loop >> "$LOG_FILE" 2>&1 &
        echo "Started with PID: $!"
        ;;
    once|*)
        run_once
        ;;
esac
