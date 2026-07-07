# Project : Customer Feedback Analyzer (Gen AI)


**The problem:** A restaurant owner has dozens of customer reviews and no time to read them all. They want a simple tool: paste the reviews, click a button, and instantly see how customers feel and what they keep complaining about.

**What I built:**
- A **backend** (FastAPI) that uses Gemini to analyze one review.
- A **frontend** (Streamlit dashboard) that the owner actually clicks on. It sends every review to your backend and shows a summary.

The fun part: the frontend calls your *own* backend the same way you called the currency API in Lesson 9. You are now on both sides of the API.

---

## Architecture
```
[ Streamlit UI ]  ──(HTTP POST)──>  [ FastAPI Backend ]  ──>  [ Gemini 2.5 Flash API ]
       │                                     │
       └───(Reads/Writes)──> [ SQLite ]      └───(Enforces Schema via Pydantic)
```

---

## Step 1: Set up the project

```bash
uv init 11_project_feedback_analyzer
cd 11_project_feedback_analyzer
uv add "fastapi[standard]" google-genai python-dotenv pydantic streamlit requests
```

Put your Gemini key in a `.env` file (see `sample.env`):

```
GOOGLE_API_KEY=your_key_here
```

---

## Step 2: The backend (`api.py`)

This is almost the same as the sentiment API from Lesson 10. We just add one more field to the answer: a one-word **theme** (like "delivery" or "taste"), so the owner can see *what* people talk about.

The full code is in `api.py`. The important part is the answer shape:

```python
class Analysis(BaseModel):
    label: str   # "positive", "negative", or "neutral"
    score: int   # 1 (very bad) to 5 (very good)
    theme: str   # one word, e.g. "delivery"
```

Run the backend in its **own terminal** and leave it running:

```bash
uv run fastapi dev api.py
```

Quick test: open **http://127.0.0.1:8000/docs**, try `/analyze` with a review, and confirm you get back a label, score, and theme.

---

## Step 3: The frontend (`app.py`)

Open a **second terminal** (keep the backend running in the first one) and run:

```bash
uv run streamlit run app.py
```

Paste a few reviews (one per line) and click **Analyze**. You can copy test reviews from `sample_reviews.txt`.

The key idea in the frontend is this loop. For each review, we call our own backend and collect the answer:

```python
for review in reviews:
    try:
        response = requests.post(API_URL, json={"text": review})
        data = response.json()
        results.append({
            "review": review,
            "label": data["label"],
            "score": data["score"],
            "theme": data["theme"],
        })
    except Exception:
        # one bad review should not stop the whole batch
        results.append({"review": review, "label": "error", "score": 0, "theme": "error"})
```

Then we build a small summary the owner cares about: how many reviews, the average score, the percent that are positive, and the single theme people mention most. Finally, a **Save to database** button writes every review into a SQLite table (`feedback.db`), and a **Saved history** section reads them all back. This is the read/write database idea from Lesson 12 — now the business keeps a growing record of all feedback, not just one report.

---

## Step 4: Keep code tidy (`database.py`)

When a file gets long, we split it. All the database code (create table, save, load) lives in its own file, **`database.py`**. Then `app.py` simply imports it at the top:

```python
from database import init_db, save_results, load_history, DB_FILE
```

This is the same idea as `import requests` or `import streamlit` — except now we are importing **our own** file. The app file stays short and is about the screen; the database file is about the data. Each file has one clear job.

---

## How to run the whole thing (two terminals)

| Terminal 1 (backend) | Terminal 2 (frontend) |
|---|---|
| `uv run fastapi dev api.py` | `uv run streamlit run app.py` |
| stays running | opens in your browser |

If the frontend shows "error" rows, the most common reason is that the backend is not running. Start it first.

---

## Some Enhancements

The project works, but a real project is never "finished." Try these:

1. **Show a chart.** Use `st.bar_chart` to show how many reviews fall under each theme. (Hint: `collections.Counter` already counts them.)
2. **Filter the table.** Add a dropdown (`st.selectbox`) to show only "negative" reviews, so the owner can focus on problems first.
3. **Read from a file.** Add a button that loads `sample_reviews.txt` straight into the text box, instead of pasting by hand (Lesson 8).
4. **New backend field.** Ask Gemini for a one-line `suggestion` on how the business could fix each negative review. (Watch your tokens — keep it short!)

---

## Yeah, I did it !!

I built a two-part AI application: a backend service and a dashboard that talks to it. This is the real shape of most AI products. From here, I can swap the "analyze a review" idea for almost anything — summarize documents, tag support tickets, draft replies — and the structure stays the same.
