import streamlit as st
from app.agent import run_categorizer
import requests
import yaml
import os, sys
import sqlite3
import pandas as pd

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="Expense Categorizer", page_icon="💰", layout="wide")

# Database connection for analytics
def get_db_connection():
    conn = sqlite3.connect("data/keywords.db")
    conn.row_factory = sqlite3.Row
    return conn

# Function to get all categories from config
def get_all_categories():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'config', 'categories.yaml'), 'r') as f:
            return list(yaml.safe_load(f).keys()) + ["Unknown"]
    except FileNotFoundError:
        return ["Unknown"]

# --- Categorization Page ---
def show_categorization_page():
    st.title("💰 Expense Categorizer")
    st.write("Enter an expense description below to categorize it.")

    # Input text area for expense description
    expense_description = st.text_area(
        "Expense Description",
        placeholder="e.g., Paid for my uber ride and groceries",
        height=100
    )

    # Input for tags
    tags_input = st.text_input(
        "Tags (comma-separated)",
        placeholder="e.g., personal, business, travel"
    )

    if st.button("Categorize Expense"):
        if expense_description:
            with st.spinner("Categorizing..."):
                # Prepare the request data including tags
                request_data = {
                    "input_text": expense_description,
                    "tags": tags_input if tags_input else None
                }
                # Make a POST request to the FastAPI categorize endpoint
                try:
                    response = requests.post("http://localhost:8000/api/categorize", json=request_data)
                    response.raise_for_status() # Raise an exception for HTTP errors
                    result = response.json()
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the FastAPI server. Please ensure it is running.")
                    return
                except requests.exceptions.RequestException as e:
                    st.error(f"Error during categorization: {e}")
                    return

            st.subheader("Categorization Result:")
            if result["category"] and result["category"] != "Unknown":
                st.success(f"**Category:** {result['category']}")
            else:
                st.warning(f"**Category:** {result['category']}")

            st.info(f"**Reasoning:** {result['reasoning']}")
            if result.get("confidence_score") is not None:
                st.write(f"**Confidence Score:** {result['confidence_score']:.2f}")
            if result.get("matching_method") is not None:
                st.write(f"**Matching Method:** {result['matching_method']}")

            st.markdown("### Provide Feedback")
            st.write("Was the categorization correct? If not, please select the correct category.")

            all_categories = get_all_categories()

            corrected_category = st.selectbox(
                "Select Correct Category (if different)",
                options=["-"] + all_categories,
                index=0
            )

            if st.button("Submit Feedback"):
                if corrected_category != "-":
                    feedback_data = {
                        "input_text": expense_description,
                        "predicted_category": result['category'],
                        "corrected_category": corrected_category,
                        "reasoning": result['reasoning'],
                        "confidence_score": result.get('confidence_score', 0.0)
                    }
                    try:
                        response = requests.post("http://localhost:8000/api/feedback", json=feedback_data)
                        if response.status_code == 200:
                            st.success("Feedback submitted successfully!")
                        else:
                            st.error(f"Failed to submit feedback: {response.status_code} - {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to the feedback API. Is the FastAPI server running?")
                else:
                    st.warning("Please select a corrected category or '-' if no correction is needed.")
        else:
            st.error("Please enter an expense description to categorize.")

    st.markdown(
        """
        ---
        This application uses an AI agent to categorize expenses based on keywords and regex patterns.
        """
    )

# --- Analytics Page ---
def show_analytics_page():
    st.title("📊 Expense Categorization Analytics")
    st.write("Insights into your expense categorization.")

    conn = get_db_connection()
    df_log = pd.read_sql_query("SELECT * FROM categorization_log", conn)
    df_feedback = pd.read_sql_query("SELECT * FROM feedback", conn)
    conn.close()

    if not df_log.empty:
        st.subheader("Most Common Categories")
        category_counts = df_log['final_category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']
        st.bar_chart(category_counts.set_index('Category'))
    else:
        st.info("No categorization data available yet. Categorize some expenses first!")

    if not df_feedback.empty:
        st.subheader("Frequent Keyword Misses (Corrections)")
        # Filter for actual corrections (where predicted != corrected)
        corrections = df_feedback[df_feedback['predicted_category'] != df_feedback['corrected_category']]

        if not corrections.empty:
            # Group by input_text and count occurrences
            missed_inputs = corrections['input_text'].value_counts().reset_index()
            missed_inputs.columns = ['Expense Description', 'Correction Count']
            st.write("Top expense descriptions that required correction:")
            st.dataframe(missed_inputs)

            st.write("\nTop predicted categories that were frequently corrected:")
            missed_categories = corrections['predicted_category'].value_counts().reset_index()
            missed_categories.columns = ['Predicted Category', 'Correction Count']
            st.dataframe(missed_categories)
        else:
            st.info("No corrections recorded yet. All categorizations were accurate or no feedback was provided.")

        st.subheader("User Correction Patterns")
        if not corrections.empty:
            correction_patterns = corrections.groupby(['predicted_category', 'corrected_category']).size().reset_index(name='Count')
            correction_patterns = correction_patterns.sort_values(by='Count', ascending=False)
            st.write("How users corrected categories:")
            st.dataframe(correction_patterns)
        else:
            st.info("No correction patterns to display.")
    else:
        st.info("No feedback data available yet.")

    # --- Main App Logic ---
page = st.sidebar.selectbox("Select a page", ["Categorization", "Analytics"])

if page == "Categorization":
    show_categorization_page()
elif page == "Analytics":
    show_analytics_page()
