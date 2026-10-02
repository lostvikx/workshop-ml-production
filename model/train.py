import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

df = pd.read_csv("dataset/imdb_dataset_review_classification.csv")
df = df.drop_duplicates()

df["review"] = df["review"].fillna("").astype(str)
df = df[df["review"].str.strip() != ""]

df["sentiment"] = df["sentiment"].map({"negative": 0, "positive": 1})

x = df["review"]
y = df["sentiment"]

x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, stratify=y, random_state=42
)

model_pipe = Pipeline(
    [
        (
            "vetorize",
            TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                sublinear_tf=True,
            ),
        ),
        (
            "classifier",
            LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        ),
    ]
)

if __name__ == "__main__":
    print("Training...")
    model_pipe.fit(x_train, y_train)

    model_file = "model/imdb_clf.joblib"
    joblib.dump(model_pipe, model_file, compress=3)

    print(f"model saved: {model_file}")
