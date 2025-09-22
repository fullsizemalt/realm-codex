\
#!/usr/bin/env python3
import os, sys, re, yaml

REQ_KEYS = ["title", "author", "date", "realm", "env", "attribution"]

def has_front_matter(text):
    return text.startswith("---\n") and "\n---" in text[4:]

def parse_front_matter(text):
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    yml = text[4:end]
    body = text[end+4:]
    try:
        data = yaml.safe_load(yml) or {}
    except Exception as e:
        raise SystemExit(f"Front matter YAML parse error: {e}")
    return data, body

def is_markdown(path):
    return path.endswith(".md") and not os.path.basename(path).startswith(".")

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "docs"
    failures = 0
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not is_markdown(fn):
                continue
            full = os.path.join(dirpath, fn)
            text = open(full, encoding="utf-8").read()
            if not text.strip():
                print(f"::warning file={full}::empty markdown file")
                continue
            if not has_front_matter(text):
                print(f"::error file={full}::missing YAML front matter (--- ... ---) with required keys {REQ_KEYS}")
                failures += 1
                continue
            data, _ = parse_front_matter(text)
            if data is None:
                print(f"::error file={full}::invalid front matter delimiters")
                failures += 1
                continue
            # Check required keys
            missing = [k for k in REQ_KEYS if k not in data]
            if missing:
                print(f"::error file={full}::missing keys in front matter: {missing}")
                failures += 1
            # Basic env validation
            if "env" in data and data["env"] not in ("dev","stg","prod","all"):
                print(f"::error file={full}::env must be dev|stg|prod|all")
                failures += 1
            # Attribution must be a non-empty list
            if "attribution" in data:
                if not isinstance(data["attribution"], list) or not data["attribution"]:
                    print(f"::error file={full}::attribution must be a non-empty list of sources")
                    failures += 1
            # Date sanity
            # (We allow any string; advanced validation can be added later)
    if failures:
        print(f"::error ::docs_metadata_lint failed with {failures} error(s).")
        sys.exit(1)
    print("docs_metadata_lint passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
