# Colonial News

Generates a daily edition of *The Pennsylvania Gazette* for the same month and day in 1776, written by the Claude Code CLI and rendered to a parchment-style HTML page.

## Requirements

- Python 3 and `jinja2` (`pip3 install -r requirements.txt`)
- Claude Code CLI (`claude`) installed, on `PATH`, and signed in. No API key is used; the script calls `claude -p … --model claude-opus-4-6 --output-format json`.

## Run once

```bash
pip3 install -r requirements.txt
python3 generate_newspaper.py
```

Output goes to `newspapers/YYYY-MM-DD.html` and `newspapers/today.html` (open in a browser). Logs go to `newspaper.log`. Both are git-ignored.

## Run every morning (Linux cron)

```bash
sudo bash setup.sh
```

This installs `jinja2`, creates `newspapers/`, and writes `/etc/cron.d/colonial-news` to run the generator at 5:00 AM (system time zone) as the user who ran `sudo`. To remove it: `sudo rm /etc/cron.d/colonial-news`.

## Files

- `generate_newspaper.py` — date mapping, prompt, claude CLI call, JSON parsing, rendering
- `templates/newspaper.html` — Jinja2 template (masthead, columns, classifieds)
- `setup.sh` — dependency install and cron setup
