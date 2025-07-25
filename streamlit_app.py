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

# Add custom CSS for mobile-first responsive design
st.markdown("""
<style>
    /* Main container adjustments */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Responsive typography */
    h1, h2, h3 {
        font-size: 1.8rem;
    }
    p, div, span {
        font-size: 1rem;
    }

    /* Media query for smaller screens (mobile-first approach) */
    @media (max-width: 600px) {
        .main .block-container {
            padding-top: 1rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        h1, h2, h3 {
            font-size: 1.5rem;
        }
        p, div, span {
            font-size: 0.9rem;
        }
        /* Make buttons and inputs full-width on small screens */
        .stButton>button, .stTextInput>div>div>input {
            width: 100%;
        }
    }
</style>
""", unsafe_allow_html=True)

# Database connection for analytics
def get_db_connection():
    conn = sqlite3.connect("data/keywords.db")
    conn.row_factory = sqlite3.Row
    return conn

# Function to get all categories from config
def get_all_categories():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'app', 'config', 'categories.yaml'), 'r') as f:
            return list(yaml.safe_load(f).keys()) + ["Unknown"]
    except FileNotFoundError:
        return ["Unknown"]

# Session management
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'last_categorized_expense' not in st.session_state:
    st.session_state.last_categorized_expense = None
if 'last_categorization_result' not in st.session_state:
    st.session_state.last_categorization_result = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Categorization"

def start_new_session():
    try:
        response = requests.post("http://localhost:8000/api/sessions")
        response.raise_for_status()
        session_data = response.json()
        st.session_state.session_id = session_data["session_id"]
        st.success(f"New session started: {st.session_state.session_id}")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the FastAPI server. Please ensure it is running.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error starting session: {e}")


# --- Categorization Page ---
def show_categorization_page():
    st.title("💰 Expense Categorizer")
    st.write("Enter an expense description below to categorize it.")

    if st.session_state.session_id is None:
        st.info("No active session. Please start a new session.")
        if st.button("Start New Session"):
            start_new_session()
            st.rerun()
        return
    else:
        st.sidebar.success(f"Active Session ID: {st.session_state.session_id}")

    # Input text area for expense description
    expense_description = st.text_area(
        "Expense Description",
        placeholder="e.g., Paid for my uber ride and groceries",
        height=100,
        key="expense_input" # Add a key to persist input
    )

    if st.button("Categorize Expense"):
        if expense_description:
            with st.spinner("Categorizing..."):
                request_data = {
                    "input_text": expense_description,
                }
                try:
                    response = requests.post(
                        "http://localhost:8000/api/categorize",
                        json=request_data,
                        params={"session_id": st.session_state.session_id}
                    )
                    response.raise_for_status()
                    result = response.json()
                    
                    # Store the last categorization details in session state
                    st.session_state.last_categorized_expense = expense_description
                    st.session_state.last_categorization_result = result

                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the FastAPI server. Please ensure it is running.")
                    return
                except requests.exceptions.RequestException as e:
                    st.error(f"Error during categorization: {e}")
                    return
        else:
            st.error("Please enter an expense description to categorize.")

    # Display categorization result and feedback section if a result exists in session state
    if st.session_state.last_categorization_result:
        result = st.session_state.last_categorization_result
        expense_description = st.session_state.last_categorized_expense

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
            index=0,
            key="feedback_selectbox" # Add a key
        )

        if st.button("Submit Feedback", key="submit_feedback_button"):
            if corrected_category != "-":
                feedback_data = {
                    "input_text": expense_description,
                    "predicted_category": result['category'],
                    "corrected_category": corrected_category,
                    "reasoning": result['reasoning'],
                    "confidence_score": result.get('confidence_score', 0.0)
                }
                try:
                    response = requests.post(
                        "http://localhost:8000/api/feedback",
                        json=feedback_data,
                        params={"session_id": st.session_state.session_id}
                    )
                    response.raise_for_status()
                    if response.status_code == 200:
                        st.success("Feedback submitted successfully!")
                    else:
                        st.error(f"Failed to submit feedback: {response.status_code} - {response.text}")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the feedback API. Is the FastAPI server running?")
                except requests.exceptions.RequestException as e:
                    st.error(f"An error occurred during feedback submission: {e}")
            else:
                st.warning("Please select a corrected category or '-' if no correction is needed.")
                

    st.markdown(
        """
        ---
        This application uses an AI agent to categorize expenses based on keywords and regex patterns and LLM as fallback when keywords are not found.
        """
    )

# --- Custom Categories Page ---
def show_custom_categories_page():
    st.title("📚 Custom Categories & Keywords")
    st.write("Manage your personal expense categorization rules.")

    user_id = st.session_state.session_id # Using session_id as user_id for simplicity

    if not user_id:
        st.warning("Please start a session on the Categorization page to manage custom categories.")
        return

    st.subheader(f"Keywords for User: {user_id}")

    # Fetch and display existing keywords
    try:
        response = requests.get(f"http://localhost:8000/api/keywords", params={"user_id": user_id})
        response.raise_for_status()
        keywords = response.json()
        if keywords:
            st.dataframe(keywords)
        else:
            st.info("No custom keywords found for this user. Add some below!")
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the FastAPI server. Please ensure it is running.")
        return
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching keywords: {e}")
        return

    st.subheader("Add New Custom Keyword")
    with st.form("new_keyword_form"):
        new_keyword = st.text_input("Keyword (e.g., 'Starbucks')")
        new_category = st.text_input("Category (e.g., 'Coffee')")
        submitted = st.form_submit_button("Add Keyword")

        if submitted:
            if new_keyword and new_category:
                try:
                    add_response = requests.post(
                        "http://localhost:8000/api/keywords",
                        json={
                            "user_id": user_id,
                            "keyword": new_keyword,
                            "category": new_category
                        }
                    )
                    add_response.raise_for_status()
                    st.success(f"Keyword '{new_keyword}' added to category '{new_category}'!")
                    st.rerun()
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the FastAPI server. Please ensure it is running.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error adding keyword: {e}")
            else:
                st.warning("Please enter both a keyword and a category.")

# --- Analytics Page ---
def show_analytics_page():
    st.title("📊 Expense Categorization Analytics")
    st.write("Insights into your expense categorization.")

    conn = get_db_connection()
    df_log = pd.read_sql_query("SELECT * FROM categorization_log", conn)
    df_feedback = pd.read_sql_query("SELECT * FROM feedback", conn)
    df_sessions = pd.read_sql_query("SELECT * FROM sessions", conn)
    df_interactions = pd.read_sql_query("SELECT * FROM interactions", conn)
    df_categorized_expenses = pd.read_sql_query("SELECT * FROM categorized_expenses", conn)
    conn.close()

    st.subheader("Overall Categorization Log")
    if not df_log.empty:
        st.dataframe(df_log)
    else:
        st.info("No categorization log data available yet.")

    st.subheader("Sessions Overview")
    if not df_sessions.empty:
        st.dataframe(df_sessions)
    else:
        st.info("No session data available yet.")

    st.subheader("Interactions Log")
    if not df_interactions.empty:
        st.dataframe(df_interactions)
    else:
        st.info("No interaction data available yet.")

    st.subheader("Categorized Expenses Log")
    if not df_categorized_expenses.empty:
        st.dataframe(df_categorized_expenses)

        st.subheader("Most Common Categories (from Categorized Expenses)")
        category_counts = df_categorized_expenses['category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']
        st.bar_chart(category_counts.set_index('Category'))

        st.subheader("Total Amount by Category")
        if 'amount' in df_categorized_expenses.columns:
            amount_by_category = df_categorized_expenses.groupby('category')['amount'].sum().reset_index()
            amount_by_category.columns = ['Category', 'Total Amount']
            st.bar_chart(amount_by_category.set_index('Category'))
        else:
            st.info("Amount column not available in categorized expenses for this analysis.")

    else:
        st.info("No feedback data available yet.")

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
# Removed st.sidebar.selectbox and replaced with buttons
st.sidebar.title("Navigation")
if st.sidebar.button("Categorization", key="nav_categorization"):
    st.session_state.current_page = "Categorization"
if st.sidebar.button("Analytics", key="nav_analytics"):
    st.session_state.current_page = "Analytics"
if st.sidebar.button("Custom Categories", key="nav_custom_categories"):
    st.session_state.current_page = "Custom Categories"

if st.session_state.current_page == "Categorization":
    show_categorization_page()
elif st.session_state.current_page == "Analytics":
    show_analytics_page()
elif st.session_state.current_page == "Custom Categories":
    show_custom_categories_page()