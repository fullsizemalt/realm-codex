#!/usr/bin/env python3
import os, re, json, requests, pathlib

CHRONICLE_PATH = os.environ.get("CHRONICLE_PATH", "docs/chronicle.md")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
SHA = os.environ.get("GITHUB_SHA", "")[:7]
RUN_URL = os.environ.get("GITHUB_SERVER_URL", "https://github.com") + f"/{REPO}/actions"
COMMIT_URL = os.environ.get("GITHUB_SERVER_URL", "https://github.com") + f"/{REPO}/commit/" + os.environ.get("GITHUB_SHA","")

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
MATRIX_HOMESERVER = os.environ.get("MATRIX_HOMESERVER", "")   # e.g., https://matrix-client.matrix.org
MATRIX_TOKEN = os.environ.get("MATRIX_ACCESS_TOKEN", "")
MATRIX_ROOM = os.environ.get("MATRIX_ROOM_ID", "")             # e.g., !roomid:server

def parse_latest_entry(md):
    # Find first front-matter block and title/author/date
    m = re.search(r"^---\n([\s\S]*?)\n---", md, flags=re.M)
    front = {}
    if m:
        y = m.group(1)
        for line in y.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                front[k.strip()] = v.strip().strip('"')
    title = front.get("title", "Handoff Update")
    author = front.get("author", "unknown")
    date = front.get("date", "")
    return title, author, date

def send_discord(title, author, date):
    if not DISCORD_WEBHOOK:
        print("No DISCORD_WEBHOOK_URL; skipping Discord")
        return
    content = f"**{title}**\nby *{author}* on {date}\nCommit: {COMMIT_URL}"
    r = requests.post(DISCORD_WEBHOOK, json={"content": content}, timeout=10)
    r.raise_for_status()
    print("Sent Discord notification.")

def send_matrix(title, author, date):
    if not (MATRIX_HOMESERVER and MATRIX_TOKEN and MATRIX_ROOM):
        print("Matrix env not fully set; skipping Matrix")
        return
    # Create client API URL
    url = MATRIX_HOMESERVER.rstrip("/") + f"/_matrix/client/v3/rooms/{MATRIX_ROOM}/send/m.room.message"
    headers = {"Authorization": f"Bearer {MATRIX_TOKEN}"}
    body = {
        "msgtype": "m.text",
        "format": "org.matrix.custom.html",
        "body": f"{title} — {author} — {date} — {COMMIT_URL}",
        "formatted_body": f"<b>{title}</b><br/>by <i>{author}</i> on {date}<br/><a href='{COMMIT_URL}'>Commit</a>"
    }
    r = requests.post(url, headers=headers, json=body, timeout=10)
    r.raise_for_status()
    print("Sent Matrix notification.")

def main():
    path = pathlib.Path(CHRONICLE_PATH)
    if not path.exists():
        raise SystemExit(f"Missing chronicle at {path}")
    md = path.read_text(encoding="utf-8")
    title, author, date = parse_latest_entry(md)
    send_discord(title, author, date)
    send_matrix(title, author, date)

if __name__ == "__main__":
    main()
