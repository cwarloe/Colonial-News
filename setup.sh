#!/usr/bin/env bash
# ============================================================
# Colonial News — Setup Script
# ============================================================
# Installs Python dependencies and configures the 5 AM cron job.
# Uses Claude Code CLI for content generation — no API key needed.
#
# Usage:
#   sudo bash setup.sh          # (sudo needed to write /etc/cron.d/)
#
# To generate today's paper immediately:
#   python3 generate_newspaper.py
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_FILE="/etc/cron.d/colonial-news"
PYTHON_BIN="$(command -v python3)"
LOG="$SCRIPT_DIR/newspaper.log"
# Run the job as the user who invoked sudo: the claude CLI is signed in per user.
CRON_USER="${SUDO_USER:-$(id -un)}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  The Pennsylvania Gazette — Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ─── Check claude CLI ──────────────────────────────────────
# (Checked before resolving the path: under `set -e` a failed `which` would
# exit silently before this message.)
if ! command -v claude &> /dev/null; then
  echo "ERROR: 'claude' CLI not found."
  echo "  Install Claude Code and ensure it is in your PATH."
  echo "  (With sudo, PATH may differ — try: sudo env PATH=\"\$PATH\" bash setup.sh)"
  exit 1
fi
CLAUDE_BIN="$(command -v claude)"
CLAUDE_DIR="$(dirname "$CLAUDE_BIN")"
echo "✓ claude CLI found: $CLAUDE_BIN"

# ─── Install Python dependencies ────────────────────────────
echo "Installing Python dependencies…"
pip3 install -r "$SCRIPT_DIR/requirements.txt"
echo ""

# ─── Create newspapers directory ────────────────────────────
mkdir -p "$SCRIPT_DIR/newspapers"
echo "Created: $SCRIPT_DIR/newspapers/"

# ─── Install cron job ───────────────────────────────────────
echo ""
echo "Writing cron job to $CRON_FILE …"

cat > "$CRON_FILE" << EOF
# The Pennsylvania Gazette — Colonial Newspaper Generator
# Runs daily at 5:00 AM

SHELL=/bin/bash
PATH=${CLAUDE_DIR}:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# The script already writes its own log to newspaper.log; only stderr
# (e.g. tracebacks) is appended here so lines are not logged twice.
0 5 * * * ${CRON_USER} cd ${SCRIPT_DIR} && ${PYTHON_BIN} generate_newspaper.py > /dev/null 2>> ${LOG}
EOF

chmod 644 "$CRON_FILE"
echo "Cron job installed: $CRON_FILE (runs as $CRON_USER)"
echo ""

# ─── Summary ────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Generate today's paper right now:"
echo "     python3 $SCRIPT_DIR/generate_newspaper.py"
echo ""
echo "  Your newspapers will appear in:"
echo "     $SCRIPT_DIR/newspapers/"
echo ""
echo "  Today's paper (always current):"
echo "     $SCRIPT_DIR/newspapers/today.html"
echo "     Open this file in your browser"
echo ""
echo "  Automatic generation: every day at 5:00 AM"
echo "     Cron entry: $CRON_FILE"
echo ""
echo "  Logs:"
echo "     $LOG"
echo ""
