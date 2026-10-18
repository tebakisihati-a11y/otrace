#!/bin/bash
# Otrace SSH Access Setup — personal token-based access
# Creates SSH keypair + token auth for remote otrace CLI access

set -e

echo "=== Otrace SSH Access Setup ==="

KEY_DIR="$HOME/.otrace"
mkdir -p "$KEY_DIR"
chmod 700 "$KEY_DIR"

# 1. Generate SSH keypair (ed25519, no passphrase for automation)
if [ ! -f "$KEY_DIR/id_ed25519" ]; then
    ssh-keygen -t ed25519 -f "$KEY_DIR/id_ed25519" -N "" -C "otrace-$(whoami)@$(hostname)"
    echo "✓ SSH keypair generated"
else
    echo "✓ SSH keypair already exists"
fi

# 2. Generate access token
TOKEN=$(head -c 32 /dev/urandom | base64 | tr -d '/+=' | head -c 32)
echo "$TOKEN" > "$KEY_DIR/access_token"
chmod 600 "$KEY_DIR/access_token"
echo "✓ Access token generated"

# 3. Setup SSH authorized_keys
cat "$KEY_DIR/id_ed25519.pub" >> "$HOME/.ssh/authorized_keys"
chmod 600 "$HOME/.ssh/authorized_keys"
echo "✓ SSH authorized_keys updated"

# 4. Create wrapper script
WRAPPER="$HOME/bin/otrace-ssh"
cat > "$WRAPPER" << 'WRAP_EOF'
#!/bin/bash
# Otrace SSH wrapper — personal access
# Usage: otrace-ssh <command> [args]
# Token required: ~/.otrace/access_token

TOKEN_FILE="$HOME/.otrace/access_token"
if [ ! -f "$TOKEN_FILE" ]; then
    echo "Access token not found. Run: bin/setup-access.sh"
    exit 1
fi

TOKEN=$(cat "$TOKEN_FILE")
HOST="${OTRACE_HOST:-localhost}"
PORT="${OTRACE_PORT:-22}"

ssh -i "$HOME/.otrace/id_ed25519" \
    -p "$PORT" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    "$(whoami)@$HOST" \
    "OTRACE_TOKEN=$TOKEN otrace $*"
WRAP_EOF
chmod +x "$WRAPPER"
echo "✓ SSH wrapper created: $WRAPPER"

# 5. Create local access wrapper
LOCAL="$HOME/bin/otrace-local"
cat > "$LOCAL" << 'LOC_EOF'
#!/bin/bash
# Otrace local wrapper — direct CLI access
# Usage: otrace-local <command> [args]

OTRACE_DIR="/Volumes/MORVEXA-CLOUD/SHARED-DATA/iCloud-Drive/Free cloud Host/otrace"
export PATH="$HOME/bin:$PATH"

cd "$OTRACE_DIR" || exit 1
exec python3 -m otrace "$@"
LOC_EOF
chmod +x "$LOCAL"
echo "✓ Local wrapper created: $LOCAL"

echo ""
echo "=== Access Information ==="
echo "SSH Key:     $KEY_DIR/id_ed25519"
echo "Public Key:  $KEY_DIR/id_ed25519.pub"
echo "Token:       $TOKEN"
echo "Local:       otrace-local <cmd>"
echo "Remote:      otrace-ssh <cmd> (set OTRACE_HOST/OTRACE_PORT)"
echo ""
echo "=== Security ==="
echo "Token file:  $KEY_DIR/access_token (chmod 600)"
echo "SSH key:     $KEY_DIR/id_ed25519 (chmod 600)"
echo "Key dir:     $KEY_DIR (chmod 700)"
