# TikTok Content Factory

> **Deploying to HEX?** Start with [`START_HERE.md`](START_HERE.md), then have the HEX-connected ChatGPT agent execute [`HEX_DEPLOYMENT_PROMPT.md`](HEX_DEPLOYMENT_PROMPT.md).

Standalone, mobile-first content generator for six-slide TikTok quote carousels. No n8n.

The app turns timely UK context into three ranked six-slide drafts, lets you edit one on your phone, then generates only that post's six photographic backgrounds and applies the final text deterministically.

## The workflow

```text
Current UK context + optional hints
            ↓
Generate 12 concepts
            ↓
Independent ranking
            ↓
Top 3 six-slide drafts
            ↓
YOU review/edit one
            ↓
Generate only its 6 backgrounds
            ↓
Pillow applies exact text at 1080×1920
            ↓
Caption + music-search hints + JPGs
            ↓
Choose a TikTok-native sound and publish
```

This approval gate is deliberate: text generation is cheap; image generation is the expensive part.

## What is built

- Mobile-first web UI at `/`
- FastAPI backend
- OpenAI Responses API for concepts, ranking, copy and optional current-web context
- GPT Image 2 for backgrounds
- Pillow for exact typography and branding
- SQLite for draft batches, rendered posts and later performance metrics
- Mock mode for zero-cost testing
- Native daily scheduler: prepare three text drafts each morning without n8n
- Docker deployment

Current model defaults are `gpt-5.6-luna` for cost-sensitive text generation and `gpt-image-2` for images. They are configurable through environment variables.

## Local run

Python 3.11+:

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -e '.[dev]'
cp .env.example .env     # Windows: copy .env.example .env
uvicorn app.api:app --reload --port 8787
```

Open `http://localhost:8787`.

### First test with no API spend

Leave **Mock mode** switched on in the UI. Generate three drafts, open one and render it. The full storage and image-rendering flow runs locally.

## Live OpenAI mode

Put the API key created through OpenAI Platform into the host's local `.env` as `OPENAI_API_KEY`. The key must never be committed.

Then:

```env
MOCK_OPENAI=false
ACCOUNT_HANDLE=@yourhandle
```

Restart the app and untick **Mock mode** in the UI.

The app can optionally use OpenAI web search to build a concise current UK context briefing before concept generation. It treats current context as context; it does not pretend something is a TikTok trend without evidence.

## Daily automatic draft generation

The app has its own scheduler. It prepares three **text drafts only** at the configured time and saves them to SQLite. They appear under **Drafts already waiting** in the UI.

```env
AUTO_PREPARE_ENABLED=true
AUTO_PREPARE_TIME=07:00
AUTO_PREPARE_TIMEZONE=Europe/London
AUTO_PREPARE_WEB_CONTEXT=true
AUTO_PREPARE_MOCK=false
```

Keep a single application worker when using the built-in scheduler. Multiple workers would each run a scheduler.

The scheduler deliberately does **not** generate images. You select/edit a draft first, then press **Generate the 6 images**.

## Docker

```bash
cp .env.example .env
# add OPENAI_API_KEY and set ACCOUNT_HANDLE
docker compose up -d --build
```

Open `http://<host>:8787`.

`output/` and `data/` persist on the host.

## API

Generate and rank three drafts without images:

```bash
curl -X POST http://localhost:8787/concepts \
  -H "Content-Type: application/json" \
  -d '{
    "manual_trends": ["Sunday evening"],
    "use_web_context": true,
    "output_post_count": 3,
    "mock": false
  }'
```

Render one approved concept:

```text
POST /drafts/{batch_id}/{concept_id}/render
```

The body can contain an edited `CarouselDraft`; the web UI handles this automatically.

Recent batches:

```text
GET /drafts?limit=10
```

Health/config state:

```text
GET /health
```

## Performance feedback

Record post results:

```text
POST /metrics
```

Fields:

```json
{
  "post_id": "...",
  "views": 12000,
  "likes": 900,
  "comments": 75,
  "shares": 420,
  "saves": 510,
  "followers_gained": 84,
  "audio_used": "manual label"
}
```

Top posts by share/save rate:

```text
GET /metrics/top?limit=10
```

The learning loop is intentionally not automatic yet. Accumulate enough real posts first, then use performance by topic, emotion, hook and payoff style to inform generation.

## Editorial rules

Every post must:

- contain exactly six slides;
- tell one coherent mini-story;
- make slide 1 the hook and slide 6 the payoff;
- use British English;
- use original wording, never fake quotations;
- avoid generic motivational clichés and engagement bait;
- avoid tragedy-jacking and polarising politics by default;
- use realistic vertical backgrounds with no text or public figures;
- keep TikTok-native music as a manual final step.

## Tests

```bash
pytest -q
ruff check app tests
```

Mock tests verify that three text drafts create no paid image work and that rendering one candidate creates exactly six final JPGs.

## HEX deployment

The repository includes `scripts/deploy_hex.sh`. It is idempotent: first run clones the deployment branch and creates `.env`; later runs pull the latest branch and rebuild the container.

On HEX:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/liamcloss/smallprojects/tiktok-content-factory/scripts/deploy_hex.sh)"
```

The first run intentionally stops after creating `~/apps/tiktok-content-factory/.env`. Add the key locally on HEX and set authentication before exposing the service:

```env
OPENAI_API_KEY=your-key-on-HEX-only
MOCK_OPENAI=false
ACCOUNT_HANDLE=@yourhandle
APP_AUTH_USERNAME=choose-a-username
APP_AUTH_PASSWORD=choose-a-long-random-password
AUTO_PREPARE_ENABLED=true
AUTO_PREPARE_TIME=07:00
AUTO_PREPARE_TIMEZONE=Europe/London
AUTO_PREPARE_WEB_CONTEXT=true
AUTO_PREPARE_MOCK=false
```

Then rerun `~/apps/tiktok-content-factory/scripts/deploy_hex.sh`.

The service binds host port `8787`. Keep that port LAN-only unless you deliberately put it behind your existing HTTPS/reverse-proxy setup. `/health` remains unauthenticated for container/network health checks; the UI, API and generated output require Basic Auth when both auth variables are set.

### Backup

The durable state is:

- `data/content_factory.sqlite3`
- `output/`
- `.env` (secret; back this up privately, never to Git)

A simple local backup before upgrades is:

```bash
cd ~/apps/tiktok-content-factory
mkdir -p backups
stamp=$(date +%Y%m%d-%H%M%S)
cp data/content_factory.sqlite3 "backups/content_factory-$stamp.sqlite3"
tar -czf "backups/output-$stamp.tar.gz" output
```
