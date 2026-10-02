(function () {
  'use strict';
    const form = document.getElementById("form");
    const textarea = document.getElementById("review");
    const submit = document.getElementById("submit");
    const error = document.getElementById("error");
    const verdict = document.getElementById("verdict");
    const verdictWord = document.getElementById("verdict-word");
    const verdictConfidence =
        document.getElementById("verdict-confidence");
    const verdictBar = document.getElementById("verdict-bar");
    const recent = document.getElementById("recent");
    const recentList = document.getElementById("recent-list");

    const RECENT_LIMIT = 5;
    let history = [];

    for (const button of document.querySelectorAll("[data-sample]")) {
        button.addEventListener("click", () => {
            textarea.value = button.dataset.sample;
            textarea.focus();
            error.textContent = "";
        });
    }

    function showError(message) {
        error.textContent = message;
    }

    function renderVerdict({ label, confidence }) {
        const percent = (confidence * 100).toFixed(1);

        verdictWord.textContent = label;
        verdictWord.parentElement.dataset.label = label;
        verdictConfidence.textContent = `${percent}%`;
        verdictBar.dataset.label = label;
        verdictBar.firstElementChild.style.width = `${percent}%`;
        verdict.hidden = false;
    }

    function renderHistory() {
        recentList.replaceChildren();
        for (const item of history) {
            const row = document.createElement("li");

            const snippet = document.createElement("span");
            snippet.className = "snippet";
            snippet.textContent = item.review;

            const tag = document.createElement("span");
            tag.className = "tag";
            tag.dataset.label = item.label;
            tag.textContent = `${item.label} ${(item.confidence * 100).toFixed(1)}%`;

            row.append(snippet, tag);
            recentList.append(row);
        }
        recent.hidden = history.length === 0;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        error.textContent = "";

        const review = textarea.value.trim();
        if (!review) {
            showError("Write a review first.");
            textarea.focus();
            return;
        }

        submit.disabled = true;
        submit.textContent = "Reading…";

        try {
            const response = await fetch("/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ review }),
            });

            if (!response.ok) {
                if (response.status === 422) {
                    showError("Write a review first.");
                } else if (response.status === 503) {
                    showError(
                        "No model loaded. Run uv run model/train.py to train it.",
                    );
                } else {
                    showError(
                        `The service returned an error (${response.status}). Try again.`,
                    );
                }
                return;
            }

            const result = await response.json();
            renderVerdict(result);
            history = [{ review, ...result }, ...history].slice(
                0,
                RECENT_LIMIT,
            );
            renderHistory();
            textarea.value = "";
        } catch {
            showError(
                "Couldn't reach the service. Check that it is running, then try again.",
            );
        } finally {
            submit.disabled = false;
            submit.textContent = "Read the review";
        }
    });
})();
