# Codex Work Prompt — TikTok Content Factory

You are the lead engineer for this repository. Work directly in the repository and leave it in a runnable, tested state. Do not just provide a plan.

## Product goal

Build a standalone, low-friction content factory for a TikTok account whose primary format is a six-image carousel of original, timely, emotionally resonant lines.

The system should turn current UK context plus evergreen human themes into strong candidate posts. Optimise for emotional recognition, carousel completion, shares, saves and follow conversion — not generic motivational content.

The intended human workflow is:

1. open the mobile web app;
2. review three ranked six-slide drafts generated for today;
3. edit/select one;
4. generate its six backgrounds;
5. choose a current TikTok-native sound;
6. publish;
7. later record performance.

There is **no n8n dependency**. Do not introduce n8n.

## Current architecture

Preserve these boundaries unless there is a strong demonstrated reason to change them:

- Python 3.11+
- FastAPI
- mobile-first server-rendered/lightweight web UI
- OpenAI Responses API for text, structured output and optional web context
- GPT Image API for photographic backgrounds
- Pillow for deterministic final 1080×1920 typography
- SQLite for draft batches, posts and metrics
- built-in single-worker daily scheduler for preparing text drafts
- Docker for deployment
- mock provider for tests and zero-cost local development

OpenAI model names are configuration. Keep defaults aligned with current official OpenAI documentation.

## Editorial contract

Every generated post must:

- contain exactly six slides;
- tell one coherent mini-story, not six unrelated quotes;
- use slide 1 as the hook and slide 6 as the save/share payoff;
- use British English;
- normally use 5–18 words per slide, hard maximum 22;
- use original wording and never fake-attribute quotations;
- avoid clichés, therapy-speak, generic hustle content and engagement bait;
- avoid tragedy-jacking and polarising politics by default;
- describe realistic vertical photographic backgrounds with no text/logos;
- keep factual/current-event context distinct from editorial interpretation;
- never claim that a sound/topic is viral without evidence.

Do not automate copyrighted audio scraping or downloading. TikTok-native audio selection remains manual.

## Current product workflow

```text
manual request OR daily scheduler
→ calendar facts + optional user hints + optional sourced current UK context
→ generate broad concept batch
→ independently rank concepts
→ draft top three as six-slide carousels
→ persist review batch
→ mobile UI review/edit
→ render only approved concept
→ generate six backgrounds
→ overlay exact text with Pillow
→ save JPGs + caption + music search terms + metadata
→ user adds TikTok-native audio and publishes
→ later record metrics
```

## Current implementation status

As of the latest run, P0, the first P1/P2 slice and the practical HEX deployment hardening are implemented:

- mock review gate tested;
- structured source provenance distinguishes calendar/manual/current-UK/TikTok-trend evidence;
- recent drafts show manual/scheduled and live/mock state;
- batches can be archived;
- duplicate active scheduled batches for a date are prevented;
- optional HTTP Basic Auth protects non-health/non-static routes;
- Windows `setup.ps1`, `configure-hex.ps1`, `update-and-run.ps1` and `stop.ps1` support the existing HEX/Tailscale pattern;
- Docker remains supported with a health check;
- 10 tests currently pass.

Do not regress these behaviours. Next useful product priority after live HEX verification is the metrics/learning loop and better editorial iteration from real post outcomes.

## Engineering priorities

### P0 — Keep the current review gate robust

- Run tests and lint first.
- Fix actual defects rather than working around them.
- Preserve mock mode.
- Confirm generating three drafts produces no image files.
- Confirm rendering one selected draft produces exactly six JPGs.
- Keep errors actionable when `OPENAI_API_KEY` is absent.
- Never print, log or commit secrets.
- Keep the mobile UI fast and usable at phone width.

### P1 — Better timely-context provenance

Introduce a structured context model that distinguishes:

- calendar/date facts;
- manual hints supplied by the user;
- sourced current UK events;
- evidence of an actual TikTok trend, if available later.

Store source title/URL/timestamp where tools expose them. Never collapse “current news/context” into “TikTok trend”.

### P2 — Daily review experience

Improve the recent-draft workflow:

- show the latest scheduled batch clearly on the home screen;
- allow dismissing/archive of weak batches;
- prevent accidental duplicate scheduled batches for the same date;
- show whether a batch came from live or mock mode;
- make generation/render errors visible without exposing internals or secrets.

### P3 — Learning loop

Once enough metrics exist, analyse performance by:

- topic;
- emotion;
- hook pattern;
- timeliness type;
- slide-six/payoff pattern;
- image style;
- manually entered audio label.

Primary rates:

- share rate = shares / views;
- save rate = saves / views;
- engagement rate = (likes + comments + shares + saves) / views;
- follow conversion = followers gained / views.

Require a sensible minimum sample before changing editorial strategy. Recommendations must be inspectable rather than silently rewriting prompts.

### P4 — Deployment hardening

- Keep one-command Docker deployment.
- Keep persistent `output/` and `data/` volumes.
- Add an optional authentication layer before exposing the UI publicly.
- Add backup/restore guidance for SQLite and output assets.
- Do not add paid infrastructure without a demonstrated need.

## Engineering standards

- Typed Pydantic models at boundaries.
- Provider interfaces for OpenAI/mock implementations.
- Structured model output rather than regex-parsed JSON.
- Version prompts in source control.
- Tests for bugs and important new paths.
- Prefer simple code to premature abstraction.
- No secret values in logs, fixtures, commits or screenshots.
- Update README and `.env.example` whenever behaviour/config changes.
- CI must use mock mode and must never require an API key.

## Definition of done for each Codex run

Do not stop at a proposal. Complete the highest-priority useful work that fits the run:

1. inspect repository state;
2. run tests/lint;
3. implement the highest-priority unfinished item;
4. add/update tests;
5. run tests/lint again;
6. update docs/config examples;
7. summarise exactly what changed, commands to run it, and remaining risks.

If live OpenAI verification is not possible, complete full mock-mode verification and say explicitly what remains unverified. Never expose an API key.
