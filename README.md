# workshop-ml-production

Sentiment classification on the [IMDB 50k movie reviews][kaggle] dataset, built
as a production-style pipeline: a scikit-learn `Pipeline` trained in a
notebook, serialized with `joblib`, and reloaded for inference.

## Dataset

[IMDB Dataset of 50k Movie Reviews][kaggle] — 50,000 labelled reviews with
columns `review` and `sentiment` (`positive` / `negative`).

Download it from Kaggle (free account required):

[kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews][kaggle]

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

## Run

```bash
uv run jupyter lab notebook.py
```

`notebook.py` is a percent-format notebook, so it opens as a notebook and also
runs top-to-bottom as a plain script:

```bash
uv run python notebook.py
```

## Pipeline

`notebook.py` runs these steps in order:

1. **Load and inspect** — shape, columns, nulls, duplicate count.
2. **Clean** — drop duplicate rows, fill null reviews, drop empty/whitespace
   reviews, keep only `review` and `sentiment`.
3. **Explore** — sentiment class distribution.
4. **Encode labels** — `negative → 0`, `positive → 1`.
5. **Split** — stratified 80/20 train/test split.
6. **Vectorize** — `TfidfVectorizer(lowercase, stop_words="english",
   ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf)`.
7. **Classify** — `LogisticRegression(max_iter=1000, class_weight="balanced",
   random_state=42)`, chained to the vectorizer in a `Pipeline`.
8. **Evaluate** — train/test accuracy, classification report, confusion matrix
   heatmap.
9. **Persist** — `joblib.dump` to `model/imdb_clf.joblib`, then reload and
   predict to confirm the roundtrip.

## Layout

```
dataset/   IMDB CSV (gitignored, download from Kaggle)
model/     trained pipeline, imdb_clf.joblib (gitignored, regenerate)
notebook.py
main.py
```

## Notes

- `random_state=42` and the stratified split make runs reproducible.
- `model/imdb_clf.joblib` is a gitignored build artifact — rerun the notebook
  to regenerate it. Loading it requires the same scikit-learn version used to
  train it; check `uv.lock` if a load fails with a version warning.

## License

Code: MIT (see [LICENSE](LICENSE)). Dataset: IMDB 50k, distributed via Kaggle
under its own terms.

[kaggle]: https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews
