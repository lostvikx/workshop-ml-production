# Frontend design: single-page sentiment form

Date: 2026-10-02
Status: awaiting review

## Goal

A single page with a form to submit a movie review and see the predicted
sentiment and confidence. No build step, no framework, no `node_modules`.

## Subject

A reader submitting text to be judged, and reading back a verdict with its
strength. The page's one job: take a review, return a verdict. Everything on it
either collects the review or reports the result.

## Stack and serving

- `app/index.html` — markup, `<style>`, and `<script>` in one file.
- Served by `main.py` via `StaticFiles(html=True)`, mounted at `/`.
- Same-origin `POST /predict`. No CORS, no dev server, no proxy.

## Routes

| Method | Path       | Response                                    |
| ------ | ---------- | ------------------------------------------- |
| `GET`  | `/`        | `app/index.html` (new)                      |
| `GET`  | `/info`    | service metadata — **moved from `/`**       |
| `GET`  | `/health`  | unchanged                                   |
| `POST` | `/predict` | unchanged                                   |

`GET /` is the only breaking change. Callers of `/` must move to `/info`.

## API contract

Unchanged. The form consumes what `POST /predict` already returns:

```json
{ "label": "Positive", "prediction": 1, "confidence": 0.7746 }
```

`label` is `Positive` or `Negative`. `confidence` is the max class
probability, 4 decimal places, already rounded server-side.

## Page structure

Single column, max ~640px, centred.

1. **Title block** — the heading "Imdb Movie Review - Sentiment Prediction",
   set at 2rem in sentence case, and one line of purpose.
2. **Sample reviews** — two buttons, one clearly positive and one clearly
   negative, drawn from the IMDB domain. Clicking fills the textarea. They
   exist so the page is testable without typing.
3. **Form** — textarea plus submit. The button says "Read the review" and keeps
   that name for the whole flow.
4. **Verdict** — label, confidence percentage, and a horizontal bar whose fill
   width is `confidence × 100`, colored by label.
5. **Recent** — last 5 predictions, newest first. In memory only; gone on
   reload. Each row: truncated review, label, percentage.

## States

- **Idle** — verdict and recent sections hidden, not shown empty.
- **Submitting** — button disabled, label becomes "Reading…". Guards against
  double submission.
- **Success** — verdict appears, review is prepended to recent, textarea is
  cleared.
- **Error** — inline message. Three distinct paths, all reachable:

| Condition  | Message                                                                  |
| ---------- | ------------------------------------------------------------------------ |
| `422`      | "Write a review first." — inline under the textarea                     |
| `503`      | Names the fix: "No model loaded. Run `uv run model/train.py` to train it." |
| network    | "Couldn't reach the service. Check that it is running, then try again."  |

Errors state what went wrong and what to do, and do not apologize.

## Visual direction

"Projector light" — pale projector glow on a screen, editorial and matte.

| Token     | Hex       | Role                                       |
| --------- | --------- | ------------------------------------------ |
| ground    | `#E4E7EC` | page background                             |
| ink       | `#1A1D23` | text                                        |
| positive  | `#1F6B45` | green, Positive label and bar fill          |
| negative  | `#A32E28` | red, Negative label and bar fill            |

Positive is green and Negative is red — the conventional mapping, which reads
faster than the original amber/slate pairing. Both clear WCAG AA against the
ground (5.2:1 and 5.7:1), so they also work at the smaller size used in the
recent-predictions list.

Type: a grotesque for the verdict word and percentages, system sans for the
form. Weight and spacing do the work; no decorative flourishes.

Restraint: the confidence bar is the one memorable element. Everything around it
is quiet. No shadows-as-decoration, no rounded-everything, no gradients.

Quality floor: responsive to mobile width, visible keyboard focus on every
interactive element, `prefers-reduced-motion` respected.

## Out of scope

Batch prediction, model history beyond the session, dark mode, i18n, any
frontend build tooling, and tests beyond a manual pass of each state.

## Files touched

- `app/index.html` — new
- `main.py` — mount static files, move `GET /` to `GET /info`
- `README.md` — document the page and the route change
