#!/usr/bin/env python3
import os, datetime, pathlib, textwrap, re

issue_number = os.environ.get("ISSUE_NUMBER", "")
issue_title  = os.environ.get("ISSUE_TITLE", "(no title)")
issue_user   = os.environ.get("ISSUE_USER", "unknown")
issue_body   = os.environ.get("ISSUE_BODY", "")
issue_labels = os.environ.get("ISSUE_LABELS", "")
repo_full    = os.environ.get("REPO_FULL", "")
closed_at    = os.environ.get("CLOSED_AT", datetime.datetime.utcnow().isoformat() + "Z")
chronicle    = pathlib.Path(os.environ.get("CHRONICLE_PATH","docs/chronicle.md"))
chronicle.parent.mkdir(parents=True, exist_ok=True)

# Normalize issue body to markdown (keep as-is)
# Optionally extract sections if present
def section(name, default=""):
    m = re.search(rf"(?mi)^##\s*{re.escape(name)}\s*\n([\s\S]*?)(?=\n##\s|\Z)", issue_body)
    return (m.group(1).strip() if m else default).strip()

state = section("Current State")
next_focus = section("Next Focus")
ask = section("Ask (Delegation)") or section("Ask")

entry = f"""
---
title: "Handoff — {issue_title}"
author: "{issue_user}"
date: "{closed_at}"
realm: "<realm-slug>"
env: "all"
attribution:
  - source: "https://github.com/{repo_full}/issues/{issue_number}"
    description: "handoff issue"
---

## State
{state or "(none provided)"}

## Next Focus
{next_focus or "(none provided)"}

## Ask
{ask or "(none provided)"}

---
"""

if chronicle.exists():
    text = chronicle.read_text(encoding="utf-8")
    if text.startswith("# "):
        lines = text.splitlines()
        new_text = "\n".join([lines[0]]) + "\n" + entry + "\n".join(lines[1:])
    else:
        new_text = entry + text
else:
    new_text = "# Chronicle (Ops Journal)\n\n" + entry

chronicle.write_text(new_text, encoding="utf-8")
print(f"✅ Appended handoff entry from issue #{issue_number} to {chronicle}")
