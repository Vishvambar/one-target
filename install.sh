#!/bin/bash
set -e

APP_DIR="$HOME/.local/share/onetarget"
BIN_DIR="$HOME/.local/bin"
BASHRC="$HOME/.bashrc"

echo "Installing One-Target Scheduler..."

# 1. Create directory
echo "Creating app directory at $APP_DIR..."
mkdir -p "$APP_DIR"

# 2. Copy schema and initialize DB
echo "Copying schema.sql..."
cp schema.sql "$APP_DIR/schema.sql"

echo "Initializing database..."
if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$APP_DIR/data.db" < "$APP_DIR/schema.sql"
else
    # Fallback if sqlite3 CLI isn't installed
    python3 -c "import sqlite3; conn=sqlite3.connect('$APP_DIR/data.db'); conn.executescript(open('$APP_DIR/schema.sql').read())"
fi

# 3. Make cli executable and symlink
echo "Setting up CLI executable..."
mkdir -p "$BIN_DIR"
cp cli.py "$APP_DIR/target"
chmod +x "$APP_DIR/target"

# Create symlink in user's local bin
ln -sf "$APP_DIR/target" "$BIN_DIR/target"

# 4. Add hook to .bashrc
HOOK_CMD="target --hook"
if ! grep -q "$HOOK_CMD" "$BASHRC"; then
    echo "Adding hook to $BASHRC..."
    echo "" >> "$BASHRC"
    echo "# One-Target Scheduler Hook" >> "$BASHRC"
    echo "$HOOK_CMD" >> "$BASHRC"
else
    echo "Hook already present in $BASHRC."
fi

echo ""
echo "Installation complete!"
echo "Please restart your terminal or run: source ~/.bashrc"
echo "If '$BIN_DIR' is not in your PATH, you may need to add it to your ~/.bashrc:"
echo '  export PATH="$HOME/.local/bin:$PATH"'
echo ""
echo "Try setting your first target with:"
echo "  target set \"My first target\""
