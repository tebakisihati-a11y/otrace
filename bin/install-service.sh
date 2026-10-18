#!/bin/bash
# Otrace Auto-Start Service
# Auto-start: launchctl load ~/Library/LaunchAgents/com.otrace.daemon.plist
# Auto-stop:  launchctl unload ~/Library/LaunchAgents/com.otrace.daemon.plist
# Status:     launchctl list | grep otrace

set -e

echo "=== Otrace NOC Service Installer ==="

# 1. Create LaunchAgent plist
PLIST="$HOME/Library/LaunchAgents/com.otrace.daemon.plist"
mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.otrace.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /Volumes/MORVEXA-CLOUD/SHARED-DATA/iCloud-Drive/Free\ cloud\ Host/otrace && python3 -m otrace schedule --daemon 2>&1 &gt;&gt; ~/Library/Logs/otrace.log</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/user/Library/Logs/otrace.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/user/Library/Logs/otrace-error.log</string>
    <key>ProcessType</key>
    <string>Background</string>
    <key>LowPriorityIO</key>
    <true/>
</dict>
</plist>
PLIST_EOF

echo "✓ LaunchAgent plist created: $PLIST"

# 2. Create log directory
mkdir -p "$HOME/Library/Logs"
touch "$HOME/Library/Logs/otrace.log"
touch "$HOME/Library/Logs/otrace-error.log"
echo "✓ Log files created"

# 3. Load the service
launchctl load "$PLIST" 2>&1 || true
echo "✓ Service loaded"

# 4. Verify
sleep 1
if launchctl list | grep -q "com.otrace.daemon"; then
    echo "✓ Service is running"
else
    echo "⚠ Service not loaded. Run: launchctl load $PLIST"
fi

echo ""
echo "=== Service Commands ==="
echo "Start:   launchctl load $PLIST"
echo "Stop:    launchctl unload $PLIST"
echo "Status:  launchctl list | grep otrace"
echo "Logs:    tail -f ~/Library/Logs/otrace.log"
echo "Errors:  tail -f ~/Library/Logs/otrace-error.log"
