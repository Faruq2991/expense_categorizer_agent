
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from app.agent import run_categorizer

st.set_page_config(page_title="Expense Categorizer", page_icon="💰")

st.title("💰 Expense Categorizer")
st.write("Enter an expense description below to categorize it.")

# Input text area for expense description
expense_description = st.text_area(
    "Expense Description",
    placeholder="e.g., Paid for my uber ride and groceries",
    height=100
)

if st.button("Categorize Expense"):
    if expense_description:
        with st.spinner("Categorizing..."):
            result = run_categorizer(expense_description)

        st.subheader("Categorization Result:")
        if result["category"] and result["category"] != "Unknown":
            st.success(f"**Category:** {result['category']}")
        else:
            st.warning(f"**Category:** {result['category']}")

        st.info(f"**Reasoning:** {result['reasoning']}")
    else:
        st.error("Please enter an expense description to categorize.")

st.markdown(
    """
    ---
    This application uses an AI agent to categorize expenses based on keywords and regex patterns.
    """
)
