
# Runbook: Documentation & Realm Lore Pipeline

**Purpose:**  
Keep the Realm Codex (MkDocs site) always current, integrating **Chronicle entries**, **realm lore**, and **refactor docs**, with clear gates for modification.

---

## 1. Local "Live Docs"

### Start Dev Server
From repo root:
```bash
pip install mkdocs-material pyyaml
mkdocs serve -a 0.0.0.0:8000
```

→ Browse at http://localhost:8000  
MkDocs auto-reloads on any change under `docs/`.

### Chronicle Appends
- Arcanum can append to `docs/chronicle.md` when `ARCANUM_APPEND_JOURNAL=true` in `.env`.
- With `mkdocs serve` running, those entries appear live in the Chronicle page.

---

## 2. Remote Publishing (GitHub Pages)

### Workflow
`.github/workflows/docs.yml`:
```yaml
name: Publish Docs
on:
  push:
    branches: [ main ]
    paths:
      - 'docs/**'
      - 'mkdocs.yml'
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.x' }
      - run: pip install mkdocs-material
      - run: mkdocs build --strict
      - uses: actions/upload-pages-artifact@v3
        with: { path: 'site' }
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

### GitHub Config
- Repo → **Settings → Pages → Source → GitHub Actions**.
- Push to `main` with changes under `docs/` → workflow builds & publishes.

---

## 3. Realm Lore Structure

### `mkdocs.yml` nav block:
```yaml
site_name: Realm Codex
theme:
  name: material
nav:
  - Home: index.md
  - Realm Lore:
      - Overview: lore/overview.md
      - Naming: lore/naming.md
      - Spirits (Agents): lore/spirits.md
      - Rites (Runbooks): lore/rites.md
      - Chronicle (Ops Journal): chronicle.md
  - Runbooks:
      - Arcanum Orchestrator: runbooks/ai-orchestrator.md
      - Documentation Pipeline: runbooks/docs-pipeline.md
```

### Folder Layout
```
docs/
  index.md
  chronicle.md
  lore/
    overview.md
    naming.md
    spirits.md
    rites.md
  runbooks/
    ai-orchestrator.md
    docs-pipeline.md
```

---

## 4. Collaboration & Safety

### Rules for Agents (Claude, Gemini, others)
1. **Do not overwrite `docs/chronicle.md` manually.**  
   - Chronicle entries are appended automatically via Arcanum or issue-close workflow.  
   - Manual edits must preserve existing front matter + history.

2. **Realm lore (`docs/lore/*`) evolves narratively.**  
   - Gemini/Claude may propose edits, but changes must:
     - Retain symbolic alignment with realm functions.
     - Include metadata attribution.

3. **Runbooks (`docs/runbooks/*`) are gated.**  
   - Any PR changing `services/` must also update or create the corresponding runbook.  
   - Pre-commit + CI enforce metadata + attribution.

4. **Publishing is via GitHub Pages workflow only.**  
   - Agents must not bypass with custom deploys.  
   - If workflow changes are proposed, they require human review.

---

## 5. Verification

- **Local:**  
  - `mkdocs serve` reloads when `docs/` changes.  
  - New Chronicle entry visible in browser within seconds.

- **Remote:**  
  - Push → GitHub Action runs → site updates at Pages URL.  
  - Verify via Action logs + updated public site.

---

## 6. Handoff Protocol

When an agent proposes a change to Realm documentation:

- Provide **diff** (`git diff`)  
- State **intent**: add lore, update runbook, refine nav, etc.  
- Confirm **metadata** present (`docs_metadata_lint.py`).  
- Include **provenance** in JSON message.

**Example Arcanum handoff (to Claude):**
```json
{
  "provider":"claude",
  "message":{
    "task":"summarize runbook changes",
    "inputs":{"diff":"<patch>"},
    "constraints":{"json_only":true,"max_tokens":256},
    "provenance":[{"source":"docs/runbooks/docs-pipeline.md","why":"runbook update"}],
    "expected":"output.default",
    "return":"json"
  }
}
```

---

**Attribution**  
- Author: Archon  
- Source: Runbook drafting session  
- Description: Documenting docs/lore pipeline for safe agent collaboration
