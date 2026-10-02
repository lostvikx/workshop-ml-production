# Workshop: ML in Production

Sentiment classification on the [IMDB 50k movie reviews][kaggle] dataset, built
as a production-style pipeline: a scikit-learn `Pipeline` trained from a script,
serialized with `joblib`, served over a FastAPI endpoint, and callable from the
command line.

## Dataset

[IMDB Dataset of 50k Movie Reviews][kaggle] — 50,000 labelled reviews with
columns `review` and `sentiment` (`positive` / `negative`).

Download it from Kaggle (free account required)

Place the CSV at:

```
dataset/imdb_dataset_review_classification.csv
```

`dataset/` is gitignored — the 64 MB file is not committed. Download it once
per clone.

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

This creates `.venv` and installs the pinned dependencies from `uv.lock`
(Python 3.13).

## Train

A trained model is committed at `model/imdb_clf.joblib`, so the API and CLI work
straight after clone. Retrain with:

```bash
uv run model/train.py
```

Takes about 25 seconds and overwrites the model in place. It reads the dataset,
so the Kaggle CSV has to be in `dataset/` first.

## Predict from the CLI

```bash
uv run model/predict.py 'The Intern is a sweet, heartwarming comedy.'
```

```text
{'label': 'Positive', 'prediction': np.int64(1), 'confidence': np.float64(0.7412472650298687)}
```

The review is the one required positional argument.

## Serve

`main.py` exposes the trained pipeline over HTTP, importing
`load_model` and `predict_sentiment` from `model/predict.py` so the API and the
CLI share one inference path. The model is loaded lazily on the first
`/predict` call and cached after that, so the app starts even with no model on
disk.

Run both commands **from the repository root** — `model` is resolved as a
namespace package relative to the working directory.

```bash
uv run fastapi dev main.py          # dev server, with auto-reload
uv run uvicorn main:app             # production ASGI server
```

Interactive docs at <http://localhost:8000/docs>.

| Method | Path       | Purpose                                   |
| ------ | ---------- | ----------------------------------------- |
| `GET`  | `/`        | Service name, version, model path         |
| `GET`  | `/health`  | Liveness, and whether the model is loaded |
| `POST` | `/predict` | Sentiment for a single review             |

```bash
curl -X POST localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d '{"review":"The Intern is a sweet, heartwarming comedy."}'
```

```json
{ "label": "Positive", "prediction": 1, "confidence": 0.7412 }
```

Status codes: `422` for a blank or missing `review`, `503` when no model is
present (the app boots regardless — run `uv run model/train.py`).

## Pipeline

`model/train.py` builds and fits the pipeline in these steps:

1. **Load** — read the CSV.
2. **Clean** — drop duplicate rows, fill null reviews, drop empty/whitespace
   reviews.
3. **Encode labels** — `negative → 0`, `positive → 1`.
4. **Split** — stratified 80/20 train/test split, `random_state=42`.
5. **Vectorize** — `TfidfVectorizer(lowercase, stop_words="english",
ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf)`.
6. **Classify** — `LogisticRegression(max_iter=1000, class_weight="balanced",
random_state=42)`, chained to the vectorizer in a `Pipeline`.
7. **Persist** — `joblib.dump` to `model/imdb_clf.joblib`.

Steps 1-4 run at import time, outside the `__main__` guard, so they execute
whenever `model.train` is imported. The API imports only `model.predict` for
this reason.

## Layout

```
dataset/   IMDB CSV (gitignored, download from Kaggle)
model/     train.py, predict.py, imdb_clf.joblib (committed)
main.py
notebook.py   dataset exploration prototype, not needed to run or serve
```

## Notes

- **Retraining is reproducible, the artifact bytes are not.** `train_test_split`
  takes `random_state=42`, so a re-run trains on the same split and produces the
  same vocabulary, coefficients, and predictions. The `.joblib` file will still
  differ byte-for-byte between runs, because a `set` inside the pipeline is
  pickled in hash order and Python randomizes string hashing per process.
  Compare predictions, not file hashes.
- `model/imdb_clf.joblib` is committed so a fresh clone can serve without the
  64 MB dataset. Loading it requires the same scikit-learn version it was
  trained with; `uv.lock` pins `scikit-learn==1.9.1`, so keep the two in step.
  If a load fails with a version warning, retrain rather than trying to load an
  incompatible artifact.
- The lazy model cache is per-process, so each uvicorn worker loads the model
  once on its own. A readiness probe that only hits `/health` reports `ok`
  before the model is in memory.

## License

Code: MIT (see [LICENSE](LICENSE)). Dataset: IMDB 50k, distributed via Kaggle
under its own terms.

[kaggle]: https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews
