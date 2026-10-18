#!/bin/bash
# Otrace Health Check — runs every 5 min via launchd
# Checks: Podman, otrace import, tools, disk space, service status

set -e

OTRACE_DIR="/Volumes/MORVEXA-CLOUD/SHARED-DATA/iCloud-Drive/Free cloud Host/otrace"
LOG="$HOME/Library/Logs/otrace-health.log"
ALERT="$HOME/.otrace/alerts"

mkdir -p "$(dirname "$LOG")" "$(dirname "$ALERT")"
TS=$(date '+%Y-%m-%d %H:%M:%S')

# Podman check
if podman machine list 2>/dev/null | grep -q "Currently running"; then
    PODMAN="OK"
else
    PODMAN="DOWN"
    echo "$TS ALERT: Podman DOWN" >> "$ALERT"
fi

# otrace import check
if cd "$OTRACE_DIR" && python3 -c "import otrace" 2>/dev/null; then
    OTRACE="OK"
else
    OTRACE="FAIL"
    echo "$TS ALERT: otrace import FAIL" >> "$ALERT"
fi

# Tool count
TOOLS=$(cd "$OTRACE_DIR" && python3 -c "from otrace.tools import installed_keys; print(len(installed_keys()))" 2>/dev/null || echo "0")

# Disk usage
DISK=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')

# Service status
if launchctl list 2>/dev/null | grep -q "com.otrace.daemon"; then
    SERVICE="RUNNING"
else
    SERVICE="STOPPED"
fi

# Log
echo "$TS podman=$PODMAN otrace=$OTRACE tools=$TOOLS disk=${DISK}% service=$SERVICE" >> "$LOG"

# Trim log to 1000 lines
tail -1000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
