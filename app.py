from collections import Counter
import os
import requests
import streamlit as st

# Our own database code, kept in a separate file (database.py).
from database import init_db, save_results, load_history, DB_FILE

# The address of our own backend service.
API_URL = "http://127.0.0.1:8000/analyze"

# Make sure the table exists before the app uses it.
init_db()

st.title("📝 Customer Feedback Analyzer")
st.write("Paste your customer reviews below, one review per line.")

# ---- Feature 3: Read from a file ----
# Initialize session state for the input text if it doesn't exist
if "input_text" not in st.session_state:
    st.session_state.input_text = ""

# Button to load the sample reviews file straight into the text box
if st.button("📂 Load Sample Reviews"):
    if os.path.exists("sample_reviews.txt"):
        with open("sample_reviews.txt", "r", encoding="utf-8") as f:
            st.session_state.input_text = f.read()
    else:
        st.error("sample_reviews.txt file not found in the directory.")

# Bind the text area value to the session state variable
reviews_text = st.text_area("Reviews", value=st.session_state.input_text, height=200)

if st.button("Analyze"):
    # Split the text box into separate reviews, ignoring blank lines.
    reviews = [line.strip() for line in reviews_text.split("\n") if line.strip()]

    if not reviews:
        st.warning("Please paste or load at least one review.")
    else:
        results = []
        # ─── ADD THE SPINNER HERE ────────────────────────────────────────
        with st.spinner("🧠 Analyzing reviews with Gemini... Please wait."):
            # Go through each review and ask our backend to analyze it.
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
                except Exception as e:
                    # One bad review should not stop the whole batch.
                    print(f"Error analyzing review: {review} -> {e}") # This prints the error in your terminal
                    results.append({
                        "review": review,
                        "label": "error",
                        "score": 0,
                        "theme": "error",
                    })

        # Save results in session_state so they survive button clicks.
        st.session_state.results = results

# Show the results if we have any.
if "results" in st.session_state:
    results = st.session_state.results

    st.subheader("Results")
    
    # ---- Feature 2: Filter the table ----
    # Add a dropdown to choose between seeing all reviews or only negative ones
    filter_option = st.selectbox(
        "Filter reviews by sentiment:",
        ["All", "Negative Only"]
    )
    
    if filter_option == "Negative Only":
        filtered_results = [r for r in results if r["label"] == "negative"]
    else:
        filtered_results = results

    st.dataframe(filtered_results)

    # ---- A simple summary for the business owner ----
    scores = [r["score"] for r in results if r["label"] != "error"]
    positive = [r for r in results if r["label"] == "positive"]
    themes = [r["theme"] for r in results if r["theme"] != "error"]

    st.subheader("Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Reviews", len(results))
    if scores:
        col2.metric("Average score", round(sum(scores) / len(scores), 1))
        col3.metric("% Positive", f"{round(len(positive) / len(results) * 100)}%")

    if themes:
        # Counter tells us which theme appears most often.
        theme_counts = Counter(themes)
        top_theme = theme_counts.most_common(1)[0][0]
        st.info(f"Customers talk most about: **{top_theme}**")
        
        # ---- Feature 1: Show a chart ----
        st.write("### Reviews by Theme")
        # st.bar_chart seamlessly accepts a Counter object or dictionary
        st.bar_chart(theme_counts)

    # ---- Save the full report to the database (Lesson 12) ----
    if st.button("💾 Save to database"):
        save_results(results)
        st.success(f"Saved {len(results)} reviews to {DB_FILE}")

# ---- Show everything we have ever saved (reads from the database) ----
with st.expander("📚 Saved history (all reviews in the database)"):
    history = load_history()
    if history:
        st.write(f"Total saved so far: {len(history)}")
        st.dataframe(
            [{"review": r[0], "label": r[1], "score": r[2], "theme": r[3]} for r in history]
        )
    else:
        st.write("Nothing saved yet. Analyze some reviews and click Save.")