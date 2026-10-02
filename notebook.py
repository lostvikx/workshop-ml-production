# %%
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# %%
df = pd.read_csv("dataset/imdb_dataset_review_classification.csv")
df.head()

# %%
print(df.shape)
print(df.columns.tolist())

# %%
print("Missing Values")
print(df.isnull().sum())

# %%
print("Duplicate Rows")
print(df.duplicated().sum())

# %%
df = df.drop_duplicates()
print(df.shape)

# %%
print("Distribution")
df["sentiment"].value_counts()

# %%
df = df[["review", "sentiment"]].copy()

df["review"] = df["review"].fillna("").astype(str)
df = df[df["review"].str.strip() != ""]

print(f"Final dataset: {df.shape}")

# %%
plt.figure(figsize=(5, 5))
sns.countplot(data=df, x="sentiment")

plt.xlabel("Sentiment")
plt.ylabel("No. of Reviews")
plt.title("Review Sentiment Distribution")

plt.show()

# %%
df["sentiment"] = df["sentiment"].map({"negative": 0, "positive": 1})
df.head()

# %%
X = df["review"]
y = df["sentiment"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)

print(f"Train samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")

# %%
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

# %%
model_pipe.fit(X_train, y_train)
print("Training Complete")

# %%
y_train_pred = model_pipe.predict(X_train)
y_test_pred = model_pipe.predict(X_test)
print("Prediction Complete")

# %%
train_acc = accuracy_score(y_train, y_train_pred)
test_acc = accuracy_score(y_test, y_test_pred)

print(f"Train Accuracy: {train_acc:.4f}")
print(f"Test Accuracy: {test_acc:.4f}")

# %%
print(classification_report(y_test, y_test_pred))

# %%
cm = confusion_matrix(y_test, y_test_pred)

plt.figure(figsize=(5, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")

plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")

plt.show()


# %%
def predict_review_sentiment(review, model):
    review_pred = model.predict([review])[0]
    review_pred_label = "(Positive)" if review_pred else "(Negative)"
    review_pred_proba = model.predict_proba([review])[0]

    print(f"Review: {review}")
    print(f"Prediction: {review_pred} {review_pred_label}")
    print(f"Prediction Probability: {review_pred_proba}")


pos_review = "The Intern is a sweet, heartwarming comedy about an aging widower who takes an internship at a fashion startup."
predict_review_sentiment(pos_review, model_pipe)

# %%
import joblib

model_file = "model/imdb_clf.joblib"
joblib.dump(model_pipe, model_file, compress=3)

print(f"Model Saved: {model_file}")

# %%
loaded_model = joblib.load(model_file)
neg_review = "Digging for Fire follows a married couple who find a bone and a gun while house-sitting, triggering a disjointed weekend of separate misadventures."
predict_review_sentiment(neg_review, loaded_model)
