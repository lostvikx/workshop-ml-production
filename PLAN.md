# Deploy to Render

Goal: serve the app at `https://<name>.onrender.com` from the existing GitHub
repo, on the free plan.

Written against Render's current docs (web services, Blueprint spec, free tier,
health checks, uv support) and measured against this repo.

## What we already have

| Requirement                    | Status                                                       |
| ------------------------------ | ------------------------------------------------------------ |
| Code on GitHub, branch `main`  | Done. `origin/main` is at `6d348c4` and matches local `HEAD`. |
| `uv.lock` at repo root         | Done. Render adds `uv` automatically when it sees this file.  |
| Python version pinned          | Done. `.python-version` says `3.13`. Render reads that file.  |
| Trained model in the repo      | Done. `model/imdb_clf.joblib` is committed, so no dataset or  |
|                                | training step is needed on Render.                            |
| Binds `0.0.0.0` on `$PORT`     | Needs the start command below.                                |
| Health check under 5s          | Done. `/health` does not touch the model. See the constraint. |

Nothing else blocks the deploy. The dataset stays gitignored, so Render never
clones the 64 MB CSV.

## Measured facts

These are from this machine and are the numbers the plan turns on:

| Measurement                  | Value    | Why it matters                                  |
| ---------------------------- | -------- | ----------------------------------------------- |
| Peak RSS after model load    | 246 MB   | Fits Render's 512 MB free tier with headroom.   |
| Model load time              | 5.08 s   | Too slow to put behind a health check.          |
| Warm predict                 | 1.0 ms   | Inference is cheap; the load is the cost.       |
| TF-IDF vocabulary            | 476,733 terms | Drives the load time and memory.            |

## The one real constraint: the 5-second health check

Render requires an HTTP health check to return 2xx or 3xx **within 5 seconds**.
Our model takes **5.08 s** to load — just over the limit.

So:

- `healthCheckPath: /health` is correct, and `/health` must stay model-free. It
  already is. Do not "improve" it to report whether the model is warm.
- The model can never be pre-warmed by the health check.
- Consequence: the first `/predict` after a wake pays the ~5 s load.

This is acceptable: Render's own wake-from-sleep already takes about a minute
and shows a loading page, so 5 s on top is marginal.

Optional later: load the model at startup instead of on first request. Startup
has Render's full 15-minute deploy window, so a 5 s cost there is free, and
every request after boot would be 1 ms. The tradeoff is that the app would no
longer boot without a model present — a deliberate choice this repo currently
avoids. Not needed for a workshop deploy.

## Steps

### 1. Commit the pending `MODEL_PATH` change

`MODEL_PATH` was relative to the working directory while `APP_DIR` was resolved
from `__file__`. It now uses `__file__`, so the app works regardless of where the
start command runs from. Verified by importing the app with `cwd` set to `/tmp`
and predicting successfully.

```bash
git push origin main
```

### 2. Add `render.yaml`

Create `render.yaml` in the repo root:

```yaml
services:
  - type: web
    name: imdb-sentiment
    runtime: python
    plan: free
    buildCommand: uv sync --frozen --no-dev
    startCommand: uv run uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    autoDeployTrigger: commit
```

Field notes, against the Blueprint spec:

- `plan: free` — 0.1 CPU, 512 MB.
- `buildCommand` — `uv sync` is safe because Render adds `uv` when `uv.lock` is
  in the repo root. `--frozen` fails the build rather than silently resolving
  different versions. `--no-dev` keeps the image smaller.
- `startCommand` — `$PORT` is set by Render and defaults to `10000`. The
  `--host 0.0.0.0` is mandatory; Render cannot route to a loopback-bound server.
- `healthCheckPath` — defaults to a TCP probe if omitted. We want the HTTP probe
  so a broken app fails the deploy instead of passing on an open port.
- `autoDeployTrigger: commit` — replaces the deprecated `autoDeploy` field.

Commit and push:

```bash
git add render.yaml && git commit -m "build: add render.yaml blueprint" && git push
```

### 3. Create the service

Blueprint route (recommended — one source of truth):

1. Render Dashboard → **New** → **Blueprint**.
2. Connect GitHub, pick `lostvikx/workshop-ml-production`.
3. Render reads `render.yaml` from the repo root. Confirm the values.
4. **Apply**.

Dashboard route: **New** → **Web Service** → pick the repo, then enter the same
values by hand. Skip this if using the Blueprint.

### 4. Watch the first deploy

The build log shows `uv sync` output, then the server binding. The deploy goes
live once `/health` returns 200 — typically a couple of minutes.

## Verify

Replace `imdb-sentiment` with whatever name you chose.

```bash
BASE=https://imdb-sentiment.onrender.com

curl -s $BASE/health          # {"status":"ok","model_loaded":false}
curl -s $BASE/info            # service, version, model_path
curl -s $BASE/ | head -3      # the HTML page
curl -s -X POST $BASE/predict \
  -H 'Content-Type: application/json' \
  -d '{"review":"A thoughtful, beautifully acted film."}'
# {"label":"Positive","prediction":1,"confidence":0.7746}
```

Then open the URL in a browser and submit a review through the form.

## What to expect from the free tier

- **Sleeps after 15 minutes idle.** The first visitor after that waits about a
  minute while Render spins it up, and sees a loading page.
- **750 instance hours per month, shared across the workspace.** One service
  sleeping when unused stays well inside that.
- **Ephemeral filesystem.** Nothing is lost, because the model comes from the
  repo image rather than being written at runtime.
- **No scaling, no persistent disk, no SSH.** Not needed here.
- **Unknown:** whether Render's own health-check traffic keeps a free service
  awake. The docs do not say. If the service seems to sleep sooner than 15
  minutes, that is the reason, and there is nothing to configure.

For a demo or workshop link this is fine. If it must be reliably reachable,
change `plan: free` to a paid plan — that is the only line that changes.

## Troubleshooting

| Symptom                                      | Cause and fix                                                              |
| -------------------------------------------- | -------------------------------------------------------------------------- |
| Deploy fails, "uv: command not found"        | `uv.lock` missing or not at repo root. It is committed. Confirm the build log. |
| Deploy fails, port detection                  | `startCommand` must bind `$PORT`, not a hardcoded `8000`.                    |
| `503` on `/predict`, "Model not found"        | The `.joblib` did not make it into the image. Check `git ls-files model/`.     |
| Version warning on load, or a load failure    | `.python-version` drifted. The pickle is version-coupled — keep it committed and unchanged. |
| First request slow, later ones fast            | Expected. 5.08 s model load once, then 1 ms per request.                     |
| Health check failures during deploy            | Something is taking over 5 s. `/health` does not load the model, so this would mean a startup hang. |

## After it is live

- `render.yaml` in the repo is the source of truth; changing a value there and
  pushing updates the service.
- Roll back from the service's **Deploys** tab — instant on the last two deploys.
- Adding a custom domain later is dashboard-only, no code or config change.
