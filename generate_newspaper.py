#!/usr/bin/env python3
"""
Colonial Daily Newspaper Generator
====================================
Generates a daily edition of The Pennsylvania Gazette based on actual
historical events from 1776, matching the current day of the year.

Usage:
    python3 generate_newspaper.py

Requirements:
    Claude Code CLI must be installed and authenticated (no API key needed).
    Install deps: pip3 install jinja2
"""

import sys
import json
import subprocess
import datetime
import re
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# ─── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
TEMPLATES_DIR = SCRIPT_DIR / "templates"
NEWSPAPERS_DIR = SCRIPT_DIR / "newspapers"
LOG_FILE = SCRIPT_DIR / "newspaper.log"

# ─── Claude CLI ───────────────────────────────────────────────────────────────
CLAUDE_BIN = "claude"
MODEL = "claude-opus-4-6"

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ─── Date Helpers ─────────────────────────────────────────────────────────────

def get_historical_date() -> datetime.date:
    """Return today's calendar date mapped to 1776 (same month & day)."""
    today = datetime.date.today()
    try:
        return today.replace(year=1776)
    except ValueError:
        # Feb 29 in a modern leap year → Feb 28 in 1776 (not a leap year)
        return today.replace(year=1776, day=28)


def estimate_issue_number(historical_date: datetime.date) -> int:
    """
    Estimate the Gazette issue number for a 1776 date.
    The Pennsylvania Gazette was first published December 24, 1728.
    By 1776 it would be roughly issue ~2,467+.
    """
    base_date = datetime.date(1728, 12, 24)
    delta = historical_date - base_date
    return int(delta.days / 7) + 1  # weekly paper, roughly


# ─── Content Generation ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are the editor of The Pennsylvania Gazette, founded by Benjamin Franklin
in Philadelphia in 1728. Today is a day in the revolutionary year 1776 and you
are producing the daily edition of this distinguished newspaper.

WRITING STYLE — strictly 18th-century journalistic prose:
• Formal, rhetorical, occasionally eloquent and impassioned
• Period vocabulary: hath, doth, 'tis, wherefore, heretofore, henceforth,
  forthwith, thereof, prithee, Gentlemen, His Excellency, &c.
• Refer to: the Colonies, the Crown, the Ministry, His Majesty (with irony
  where appropriate), Patriots, Tories, the Continental Army, the Congress,
  the Committee of Safety, Redcoats, Hessian mercenaries
• Datelines in the style: "PHILADELPHIA, March 11." or "NEW-YORK, March 8."
• Prices in shillings and pence; distances in miles and furlongs
• Always spell out numbers below twenty; use numerals above

HISTORICAL ACCURACY:
• All content must be grounded in REAL events of 1776.
• Be specific: use real names (Washington, Jefferson, Adams, Franklin,
  Hancock, Howe, Burgoyne, Cornwallis, Paine, Lee, Greene, Knox, etc.)
• Reference real places, battles, acts of Parliament, Congressional
  resolutions, and military movements relevant to the given date.
• Do not invent battles that did not happen or attribute quotes to people
  who did not say them.
"""

USER_PROMPT_TEMPLATE = """\
Generate a complete edition of The Pennsylvania Gazette for {date_str}.

Vol. {volume}, No. {issue_num}

Return ONLY a valid JSON object — no markdown fences, no explanation, \
just the raw JSON. Use this exact structure:

{{
  "front_page_articles": [
    {{
      "headline": "Main headline (ALL CAPS, dramatic, period style)",
      "deck": "A secondary headline or summary line",
      "dateline": "CITY, Month Day.",
      "body": "3–4 substantial paragraphs separated by \\n\\n. \
Period prose, historically accurate.",
      "wide": true
    }},
    {{
      "headline": "Second front-page story",
      "deck": "Deck line",
      "dateline": "CITY, Month Day.",
      "body": "2–3 paragraphs",
      "wide": false
    }},
    {{
      "headline": "Third front-page story",
      "deck": "Deck line",
      "dateline": "CITY, Month Day.",
      "body": "2–3 paragraphs",
      "wide": false
    }}
  ],
  "national_news": [
    {{
      "headline": "Headline",
      "dateline": "CITY, Month Day.",
      "body": "2–3 paragraphs of colonial American news"
    }},
    {{
      "headline": "Headline",
      "dateline": "CITY, Month Day.",
      "body": "2–3 paragraphs"
    }},
    {{
      "headline": "Headline",
      "dateline": "CITY, Month Day.",
      "body": "2–3 paragraphs"
    }}
  ],
  "international_news": [
    {{
      "headline": "News from Abroad — Britain, France, etc.",
      "dateline": "LONDON, [date] (By the Last Packet)",
      "body": "2–3 paragraphs on foreign affairs"
    }},
    {{
      "headline": "Headline",
      "dateline": "CITY, date",
      "body": "2–3 paragraphs"
    }}
  ],
  "local_news": [
    {{
      "headline": "Philadelphia local news",
      "body": "1–2 paragraphs about Philadelphia civic life, commerce, or events"
    }},
    {{
      "headline": "Second local item",
      "body": "1–2 paragraphs"
    }}
  ],
  "sports_and_leisure": [
    {{
      "headline": "Horse-Racing, hunting, tavern news, or other leisure",
      "body": "1–2 paragraphs in period style"
    }},
    {{
      "headline": "Another leisure or cultural item",
      "body": "1–2 paragraphs"
    }}
  ],
  "letters_to_editor": [
    {{
      "author": "A Concerned Patriot of Pennsylvania",
      "subject": "Short subject description",
      "body": "2–3 paragraphs as a formal letter. Begin: 'To the Printer of the Gazette, SIR, ...'"
    }},
    {{
      "author": "A Freeholder of New-Jersey",
      "subject": "Short subject",
      "body": "1–2 paragraphs letter"
    }}
  ],
  "classifieds": [
    {{
      "category": "SHIPS ARRIVED",
      "text": "Brief notice about a ship's arrival with cargo details"
    }},
    {{
      "category": "RUN AWAY",
      "text": "Notice about a runaway apprentice or servant (period-typical ad)"
    }},
    {{
      "category": "FOR SALE",
      "text": "Advertisement for goods, land, livestock, or property"
    }},
    {{
      "category": "WANTED",
      "text": "Notice seeking a skilled craftsman, information, or debts owed"
    }},
    {{
      "category": "NOTICE",
      "text": "A legal, civic, or commercial notice"
    }}
  ],
  "weather": "A brief weather report for Philadelphia in period style (1–2 sentences).",
  "printers_notice": "A short note from the printer — 1 sentence. Period style."
}}

Ground ALL content in real historical events of {date_str}. \
The newspaper should feel as though it was actually printed on that date in 1776.
"""


def generate_newspaper_content(historical_date: datetime.date) -> dict:
    """Call the claude CLI to generate newspaper content for the given date."""
    date_str = historical_date.strftime("%B %d, 1776")
    issue_num = estimate_issue_number(historical_date)
    volume = 49  # approximate volume for 1776

    log.info("Calling claude CLI for %s (Vol. %d, No. %d)…", date_str, volume, issue_num)

    full_prompt = SYSTEM_PROMPT + "\n\n" + USER_PROMPT_TEMPLATE.format(
        date_str=date_str,
        volume=volume,
        issue_num=issue_num,
    )

    result = subprocess.run(
        [CLAUDE_BIN, "-p", full_prompt, "--model", MODEL, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=str(SCRIPT_DIR),
    )

    if result.returncode != 0:
        log.error("claude CLI error (exit %d): %s", result.returncode, result.stderr[:400])
        raise RuntimeError(f"claude CLI exited with code {result.returncode}")

    # The --output-format json wrapper gives: {"result": "<text>", ...}
    try:
        wrapper = json.loads(result.stdout)
        text_content = wrapper.get("result", result.stdout)
    except json.JSONDecodeError:
        text_content = result.stdout

    # Strip any markdown fences Claude might add despite instructions
    text_content = re.sub(r"^```[a-z]*\n?", "", text_content.strip())
    text_content = re.sub(r"\n?```$", "", text_content.strip())

    # Find JSON object
    json_match = re.search(r"\{[\s\S]*\}", text_content)
    if json_match:
        text_content = json_match.group(0)

    try:
        data = json.loads(text_content)
    except json.JSONDecodeError as exc:
        log.error("JSON parse error: %s", exc)
        log.error("First 600 chars of response: %s", text_content[:600])
        raise

    log.info("Content generated successfully.")
    return data


# ─── Rendering ────────────────────────────────────────────────────────────────

def render_newspaper(content: dict, historical_date: datetime.date) -> str:
    """Render newspaper content into HTML via the Jinja2 template."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )
    template = env.get_template("newspaper.html")

    day_name = historical_date.strftime("%A").upper()
    month_name = historical_date.strftime("%B").upper()
    day_num = historical_date.day
    issue_num = estimate_issue_number(historical_date)
    volume = 49

    return template.render(
        content=content,
        day_name=day_name,
        month_name=month_name,
        day_num=day_num,
        year=1776,
        issue_num=issue_num,
        volume=volume,
        historical_date=historical_date,
    )


# ─── Saving ───────────────────────────────────────────────────────────────────

def save_newspaper(html: str, date: datetime.date) -> Path:
    """Write the newspaper HTML to disk and update today.html."""
    NEWSPAPERS_DIR.mkdir(exist_ok=True)

    dated_file = NEWSPAPERS_DIR / f"{date.isoformat()}.html"
    dated_file.write_text(html, encoding="utf-8")

    today_file = NEWSPAPERS_DIR / "today.html"
    today_file.write_text(html, encoding="utf-8")

    return dated_file


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main() -> None:
    historical_date = get_historical_date()
    log.info("Generating newspaper for %s…", historical_date.strftime("%B %d, 1776"))

    content = generate_newspaper_content(historical_date)

    log.info("Rendering HTML…")
    html = render_newspaper(content, historical_date)

    output_file = save_newspaper(html, historical_date)
    log.info("Saved → %s", output_file)
    log.info("Also   → %s/today.html", NEWSPAPERS_DIR)
    log.info("Done.")


if __name__ == "__main__":
    main()
