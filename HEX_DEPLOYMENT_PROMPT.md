# HEX replacement and deployment prompt

## How to use this file

Upload the complete TikTok Content Factory ZIP to the ChatGPT conversation that has remote terminal/filesystem access to HEX, then send:

> **Execute `HEX_DEPLOYMENT_PROMPT.md` from the attached project. Treat it as authoritative. Do the work directly and continue until the service is deployed and verified.**

The remote agent should then follow the instructions below.

---

You have remote terminal/filesystem access to my Windows machine called HEX.

I want you to replace the existing repository/project currently being worked on in this chat with the attached TikTok Content Factory project.

Do the work directly. Do not just give me instructions or a plan. Continue until the replacement app is deployed and verified as far as the available access allows.

## Objective

Replace the current repo contents with the TikTok Content Factory contained in this project and deploy it on HEX.

This is a standalone Python/FastAPI application. There is no n8n dependency.

The finished service should:

- run on HEX on port `8787`;
- be accessible locally;
- be accessible over the existing HEX Tailscale connection;
- use SQLite for persistence;
- generate 3 ranked six-slide TikTok carousel drafts;
- allow mobile review/editing;
- generate six images only after a draft is approved;
- use OpenAI for live text/current-context/image generation;
- automatically prepare text drafts at 07:00 Europe/London;
- require manual approval before image generation;
- keep TikTok-native music selection and publishing manual;
- never expose or commit API keys/passwords.

## 1. Identify and protect the current repo

Use the repository/path already established in this chat.

Before replacing anything:

1. Inspect the repo location and current git status.
2. Record the current branch and HEAD commit.
3. Create a recoverable backup before deleting/replacing files.
   - Prefer a git backup branch/tag such as `backup/pre-tiktok-content-factory-YYYYMMDD-HHMM`.
   - If there are uncommitted files, preserve them in a timestamped backup outside the repo as well.
4. Do not delete `.git` unless absolutely necessary.
5. Do not delete any existing secrets merely because the working tree is being replaced.
6. Never print secret values into chat or logs.

I explicitly authorise replacing the existing application source files after the backup has been created.

## 2. Replace the working tree

Treat the attached TikTok Content Factory project as the source of truth.

Replace the current repo's application contents with the contents of this project.

Important:

- preserve `.git`;
- do not copy generated `.pytest_cache`, `__pycache__`, `.venv`, SQLite databases or rendered output;
- ensure the new repository root contains items such as:

```text
app/
tests/
scripts/
pyproject.toml
Dockerfile
docker-compose.yml
.env.example
README.md
CODEX_PROMPT.md
HEX_DEPLOYMENT_PROMPT.md
```

After replacement, inspect the resulting tree and make sure there is not an accidental extra nesting such as:

```text
repo/tiktok-content-factory/app/
```

The intended layout is:

```text
repo/app/
repo/scripts/
repo/tests/
...
```

## 3. Validate the source before deployment

Use Python 3.11+.

Create/refresh the virtual environment and dependencies using the supplied scripts where practical:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
./scripts/setup.ps1
```

Then run the project's tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Also perform an import/compile check if useful.

Do not proceed past real test failures by simply ignoring them. Diagnose and fix defects caused by the replacement/deployment environment.

The project should have a fully passing test suite before deployment.

## 4. Configure persistent HEX state

This project stores persistent HEX secrets/config outside the repository at:

```text
%LOCALAPPDATA%\TikTokContentFactory\app.env
```

First check whether that file already exists.

If it exists:

- preserve it;
- check only whether the required variable names are present/non-empty;
- DO NOT print their values.

Required live configuration is:

```text
OPENAI_API_KEY
MOCK_OPENAI=false
USE_WEB_CONTEXT=true

AUTO_PREPARE_ENABLED=true
AUTO_PREPARE_TIME=07:00
AUTO_PREPARE_TIMEZONE=Europe/London
AUTO_PREPARE_WEB_CONTEXT=true
AUTO_PREPARE_MOCK=false

APP_AUTH_USERNAME
APP_AUTH_PASSWORD
```

If an OpenAI key is already securely available on HEX, reuse it without exposing it.

If the API key is not available on HEX, continue deploying the application and verifying mock mode. Do not ask me to paste an API key into ordinary chat.

At the end, tell me the single secure local step required to add the key.

The supplied secure configuration helper is:

```powershell
./scripts/configure-hex.ps1
```

Use that if the remote terminal supports secure interactive input.

Do not commit `app.env`, `.env`, API keys or passwords.

## 5. Deploy natively on HEX

HEX already hosts other services using Windows + Python + Tailscale. Follow the same low-friction pattern rather than introducing Docker unless native deployment fails for a concrete reason.

Use:

```powershell
./scripts/update-and-run.ps1 -NoBrowser -SkipPull
```

Use `-SkipPull` for this first deployment because the working tree has just been replaced locally and may not yet exist in the remote GitHub branch.

The app should bind to:

```text
0.0.0.0:8787
```

Persistent state/logs should live under:

```text
%LOCALAPPDATA%\TikTokContentFactory\
```

Verify:

```text
http://127.0.0.1:8787/health
```

and the main UI:

```text
http://127.0.0.1:8787/
```

## 6. Verify Tailscale access

HEX already uses Tailscale.

Determine the current HEX Tailscale DNS name using the installed Tailscale client rather than assuming it.

Expected address format:

```text
http://hex.<tailnet>.ts.net:8787
```

Verify that port 8787 is reachable through the machine's Tailscale interface as far as your tooling permits.

Do not alter the working Tailscale setup unnecessarily.

If Windows Firewall blocks 8787 over Tailscale, add the narrowest appropriate rule rather than broadly opening the machine to the public internet.

This service does not need to be publicly internet-facing.

## 7. Authentication

The app supports HTTP Basic Auth.

For the HEX deployment, authentication should be enabled because the application binds to `0.0.0.0`.

`/health` should remain usable for health checking without revealing sensitive data.

Do not display the configured password.

## 8. Functional smoke test

After deployment perform an actual application smoke test.

### Mock mode

First verify the zero-cost flow:

1. open/call the app;
2. generate a mock batch;
3. confirm exactly 3 ranked drafts are returned/stored;
4. confirm no AI image files are generated merely by producing the drafts;
5. select/render one mock draft;
6. confirm exactly 6 final slide JPGs are generated.

This validates:

```text
generate -> rank -> review gate -> render
```

### Live mode

If `OPENAI_API_KEY` is available:

1. confirm `MOCK_OPENAI=false`;
2. generate one real draft batch with current UK context;
3. confirm three drafts are produced;
4. inspect them for obvious schema/editorial failures;
5. DO NOT generate six paid images merely for deployment testing unless necessary.

Avoid unnecessary API spend.

## 9. Verify scheduler

Confirm the application is configured for:

```text
07:00 Europe/London
```

The scheduler should generate TEXT DRAFTS ONLY.

It must not automatically generate images.

Ensure only one application worker is running so the built-in scheduler does not execute more than once.

Confirm duplicate scheduled batches for the same date are prevented.

## 10. Git state after successful deployment

Once the replacement app is functioning:

1. inspect `git status`;
2. make sure secrets, SQLite databases, output images, virtual environments and logs are ignored;
3. commit the replacement application to the current repository;
4. use a clear commit message, for example:

```text
Replace app with TikTok Content Factory V1
```

If the existing GitHub remote is intentionally the repository we want to continue using, push the replacement to it.

Do NOT push if doing so would overwrite an unrelated remote without the backup branch/tag having been successfully created first.

If there is uncertainty about remote intent, leave the local commit complete and report the exact remote/push decision remaining.

## 11. Final verification

Before declaring success check:

- tests pass;
- `/health` responds;
- home UI responds;
- only one service process is running;
- SQLite location is persistent;
- output directory is persistent;
- scheduler configuration is loaded;
- mock generation works;
- review gate works;
- six-image render works;
- OpenAI live generation works if a key is available;
- logs contain no secret values;
- repo contains no secret files;
- Tailscale URL is identified.

## 12. Post-deployment next steps

After the technical deployment is green:

1. Open the Tailscale/mobile URL from my phone.
2. Confirm authentication works.
3. Generate one real three-draft batch.
4. Review/edit a selected six-slide post in the UI.
5. Generate the six final images for that selected post only.
6. Download/use the six slide images in TikTok.
7. Choose a currently trending native TikTok sound manually.
8. Publish manually.
9. Record the post's performance metrics in the app when available.
10. After enough posts have data, use those metrics to tune ranking rather than changing the architecture prematurely.

Do not add automatic TikTok publishing, complex infrastructure, or n8n as part of this deployment.

## 13. Report back concisely

At the end give me:

### Deployment status

`LIVE`, `LIVE IN MOCK MODE`, or `BLOCKED`

### URLs

- Local
- Tailscale/mobile

### Verification

- tests
- health
- mock generation
- render
- live OpenAI
- scheduler

### Git

- backup branch/tag
- new commit SHA
- whether pushed

### Remaining action

Only include actions I genuinely need to perform.

Do not stop after describing commands. Execute everything you can through your remote terminal/filesystem access.
