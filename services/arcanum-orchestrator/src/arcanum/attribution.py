import os, json, datetime, pathlib
def append_chronicle_entry(action: str, provider: str, message: dict, output: dict):
    path = pathlib.Path(os.environ.get("ARCANUM_CHRONICLE_PATH","docs/chronicle.md"))
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    entry = (
        "\n---\n"
        + f"title: \"Arcanum Invoke — {provider}\"\n"
        + "author: \"arcanum\"\n"
        + f"date: \"{now}\"\n"
        + "realm: \"<realm-slug>\"\n"
        + "env: \"all\"\n"
        + "attribution:\n"
        + "  - source: \"arcanum\"\n"
        + f"    description: \"invoke {provider}\"\n"
        + "---\n\n"
        + "## Message\n```json\n" + json.dumps(message, indent=2) + "\n```\n\n"
        + "## Output\n```json\n" + json.dumps(output, indent=2) + "\n```\n\n---\n"
    )
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if text.startswith("# "):
            lines = text.splitlines()
            new_text = "\n".join([lines[0]]) + "\n" + entry + "\n".join(lines[1:])
        else:
            new_text = entry + text
    else:
        new_text = "# Chronicle (Ops Journal)\n\n" + entry
    path.write_text(new_text, encoding="utf-8")
