# Conclave Notifications for Chronicle Updates

This pack broadcasts Chronicle updates (handoffs, ops journal entries) to **Discord** and **Matrix**.

## Install
```bash
unzip handoff_notify_pack.zip -d .
git add .github/workflows/notify-handoff.yml scripts/notify_channels.py
git commit -m "feat(conclave): notify Discord/Matrix on Chronicle updates"
git push
```

## Configure Secrets (GitHub → Settings → Secrets and variables → Actions)
- `DISCORD_WEBHOOK_URL` — create an Incoming Webhook in your Discord channel
- `MATRIX_HOMESERVER` — e.g., https://matrix-client.matrix.org
- `MATRIX_ACCESS_TOKEN` — from a Matrix user account/bot
- `MATRIX_ROOM_ID` — e.g., !abc123:matrix.org

## How it works
- Workflow triggers on any push that changes `docs/chronicle.md`.
- It parses the first Chronicle entry (title/author/date) and posts:
  - Discord (webhook): simple markdown
  - Matrix (client API): HTML and plaintext

## Notes
- If you also use the **Handoff Issue → Chronicle** workflow, the notify workflow will fire after it commits the Chronicle entry.
- You can change triggering paths to include other docs.
