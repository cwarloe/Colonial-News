#!/usr/bin/env bash
# ============================================================
# Colonial News — Setup Script
# ============================================================
# Installs Python dependencies and configures the 5 AM cron job.
#
# Usage:
#   export ANTHROPIC_API_KEY='sk-ant-...'
#   sudo bash setup.sh          # (sudo needed to write /etc/cron.d/)
#
# To generate today's paper immediately:
#   python3 generate_newspaper.py
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_FILE="/etc/cron.d/colonial-news"
PYTHON_BIN="$(which python3)"
LOG="$SCRIPT_DIR/newspaper.log"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  The Pennsylvania Gazette — Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ─── Check API key ─────────────────────────────────────────
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "⚠  WARNING: ANTHROPIC_API_KEY is not set in this shell."
  echo "   The newspaper generator will not run without it."
  echo "   Set it before running: export ANTHROPIC_API_KEY='sk-ant-...'"
  echo ""
fi

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

# We store the API key in a sourced env file so cron can read it.
ENV_FILE="$SCRIPT_DIR/.env"

if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}" > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "API key saved to $ENV_FILE (mode 600)"
else
  echo "# Set your API key here:" > "$ENV_FILE"
  echo "ANTHROPIC_API_KEY=sk-ant-REPLACE_ME" >> "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "⚠  Created $ENV_FILE — please edit it and add your API key."
fi

cat > "$CRON_FILE" << EOF
# The Pennsylvania Gazette — Colonial Newspaper Generator
# Runs daily at 5:00 AM

SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

0 5 * * * root . ${ENV_FILE} && cd ${SCRIPT_DIR} && ${PYTHON_BIN} generate_newspaper.py >> ${LOG} 2>&1
EOF

chmod 644 "$CRON_FILE"
echo "Cron job installed: $CRON_FILE"
echo ""

# ─── Summary ────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📰 Generate today's paper right now:"
echo "     python3 $SCRIPT_DIR/generate_newspaper.py"
echo ""
echo "  📂 Your newspapers will appear in:"
echo "     $SCRIPT_DIR/newspapers/"
echo ""
echo "  🌅 Today's paper (always current):"
echo "     $SCRIPT_DIR/newspapers/today.html"
echo "     → Open this file in your browser"
echo ""
echo "  ⏰ Automatic generation: every day at 5:00 AM"
echo "     Cron entry: $CRON_FILE"
echo ""
echo "  📋 Logs:"
echo "     $LOG"
echo ""
