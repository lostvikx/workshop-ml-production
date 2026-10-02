import sys

import joblib


def predict_review_sentiment(review, model):
    review_pred = model.predict([review])[0]
    review_pred_label = "(Positive)" if review_pred else "(Negative)"
    review_pred_proba = model.predict_proba([review])[0]

    print(f"Review: {review}")
    print(f"Prediction: {review_pred} {review_pred_label}")
    print(f"Prediction Probability: {review_pred_proba}")


def load_model(model_file):
    model = joblib.load(model_file)
    return model


def predict_sentiment(review, model):
    review_pred = model.predict([review])[0]
    review_pred_label = "Positive" if review_pred else "Negative"
    review_pred_proba = model.predict_proba([review])[0]
    confidence = review_pred_proba[review_pred]

    return {
        "label": review_pred_label,
        "prediction": review_pred,
        "confidence": confidence,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Missing required argument.")
        print("Usage: python script.py <your_argument>")
        sys.exit(1)

    review = sys.argv[1]

    model_file = "model/imdb_clf.joblib"
    model = load_model(model_file)

    sentiment = predict_sentiment(review, model)
    print(sentiment)
