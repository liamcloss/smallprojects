# Start here

This ZIP is intended to be handed directly to the ChatGPT conversation that has remote terminal/filesystem access to HEX.

## One instruction to send to the HEX-connected chat

> **Execute `HEX_DEPLOYMENT_PROMPT.md` from the attached project. Treat it as authoritative. Do the work directly and continue until the service is deployed and verified.**

That file contains the complete replacement, backup, configuration, deployment, Tailscale, authentication, smoke-test, scheduler, git and post-deployment instructions.

## What the project does

The TikTok Content Factory is a standalone FastAPI app that:

- generates/ranks TikTok carousel concepts;
- presents 3 six-slide drafts for review;
- lets you edit the selected draft;
- generates six image backgrounds only after approval;
- renders exact quote text onto the images programmatically;
- stores history/metrics in SQLite;
- can prepare text drafts automatically at 07:00 Europe/London;
- keeps music choice and TikTok publishing manual.

There is no n8n dependency.

## Security

Do not put secrets inside the repository. On HEX, persistent credentials are stored in:

```text
%LOCALAPPDATA%\TikTokContentFactory\app.env
```

Use `scripts/configure-hex.ps1` for secure interactive configuration.
