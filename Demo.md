# Expense Categorizer Demo Guide

This guide provides a comprehensive walkthrough of the Expense Categorizer application, highlighting its core functionalities, API endpoints, and real-world value. It's designed to serve as a script for a demo video, showcasing how the application helps users efficiently categorize expenses and improve accuracy over time.

## 🚀 Real-World Value

The Expense Categorizer addresses a common pain point for individuals and small businesses: manually categorizing financial transactions. By automating this process, it offers:

*   **Time Savings**: Quickly categorize large volumes of transactions.
*   **Accuracy**: Leverage multiple matching methods (database, regex, AI) for precise categorization.
*   **Adaptability**: Improve categorization accuracy over time through user feedback, making the system smarter for your specific needs.
*   **Insight**: Gain a clear overview of spending patterns through built-in analytics.

## 🛠️ Setup and Running the Application

Before starting the demo, ensure the FastAPI backend and Streamlit frontend are running.

1.  **Start the FastAPI Backend**:
    Navigate to the project root directory (`/home/faruq/expense_categorizer_agent/`) and run:
    ```bash
    uvicorn app.main:app --reload
    ```
    (This will typically run on `http://localhost:8000`)

2.  **Start the Streamlit Frontend**:
    In a separate terminal, navigate to the project root directory and run:
    ```bash
    streamlit run streamlit_app.py
    ```
    (This will open the Streamlit app in your browser, typically on `http://localhost:8501`)

## 🎬 Demo Walkthrough

### 1. Introduction to the UI and Core Categorization

*   **Objective**: Show the main categorization interface and demonstrate how to categorize a simple expense.
*   **Action**:
    *   Open the Streamlit app in your browser.
    *   Explain the "Categorization" page.
    *   Click "Start New Session" (if prompted) to generate a session ID. Explain that this tracks user interactions.
    *   Enter an expense description in the text area, e.g., "Coffee at Starbucks".
    *   Click "Categorize Expense".
    *   **Highlight**: The result showing `Category`, `Reasoning` (e.g., "Matched using LLM"), `Confidence Score`, and `Matching Method`. Explain how the system uses a hierarchy (DB -> Regex -> LLM).

### 2. Demonstrating Different Matching Methods

*   **Objective**: Show how the DB, Regex, and LLM fallbacks work.
*   **Action**:
    *   **DB Matcher**: Enter an expense that you know is in the `data/keywords.db` (e.g., "Monthly rent payment"). Show it categorizes with "Matched using DB" and high confidence.
    *   **Regex Matcher**: Enter an expense that matches a regex pattern (e.g., "Electricity bill"). Show it categorizes with "Matched using Regex" and medium confidence.
    *   **LLM Fallback**: Enter a novel expense not covered by DB or Regex (e.g., "Subscription for cloud storage"). Show it categorizes with "Matched using LLM" and a lower confidence.

### 3. The Feedback Loop: Improving Accuracy

*   **Objective**: Show how users can correct categorizations and improve the system.
*   **Action**:
    *   Categorize an expense that was incorrectly categorized or categorized by LLM (e.g., "Dinner at a fancy restaurant" -> "Unknown" or a general category).
    *   In the "Provide Feedback" section, select the correct category from the dropdown (e.g., "Dining Out").
    *   Click "Submit Feedback".
    *   **Explain**: This feedback is stored and the system automatically adds the `input_text` as a new keyword for the `corrected_category` in the database. This means next time, this specific expense will be categorized correctly with high confidence.
    *   **Demonstrate Improvement**: Re-categorize the *exact same* expense. Show that it now uses "Matched using DB" and has high confidence.

### 4. Managing Custom Keywords

*   **Objective**: Show how users can manually add their own categorization rules.
*   **Action**:
    *   Navigate to the "Custom Categories" page using the sidebar.
    *   **Explain**: This page allows users to view and add custom keywords. Note that the current implementation allows adding but not editing/deleting from the UI.
    *   Show the existing keywords table.
    *   Use the "Add New Custom Keyword" form:
        *   Enter a `Keyword` (e.g., "My Local Cafe").
        *   Enter a `Category` (e.g., "Coffee").
        *   Click "Add Keyword".
    *   **Demonstrate**: Go back to the "Categorization" page and categorize "Coffee at My Local Cafe". Show it's now categorized correctly via DB match.

### 5. Analytics and Insights

*   **Objective**: Showcase the analytics capabilities for understanding spending and system performance.
*   **Action**:
    *   Navigate to the "Analytics" page using the sidebar.
    *   **Highlight**:
        *   **Overall Categorization Log**: Shows a history of all categorized expenses, including category, matching method, and confidence.
        *   **Categorized Expenses Log**: A detailed log of all categorized expenses.
        *   **Most Common Categories**: Bar chart visualizing spending distribution.
        *   **Frequent Keyword Misses (Corrections)**: Shows which input texts and predicted categories frequently required correction, indicating areas for system improvement.
        *   **User Correction Patterns**: Displays how predicted categories were corrected to actual categories.
    *   **Explain**: These insights help users understand their spending habits and help developers identify areas where the categorization model can be further refined.

### 6. API Endpoints (For Developers/Integrators)

*   **Objective**: Briefly explain the underlying FastAPI endpoints for integration.
*   **Action**:
    *   Mention that the application exposes a robust API for programmatic access.
    *   List key endpoints and their purpose:
        *   `POST /api/categorize`: Categorize an expense.
            *   **Request Body**: `{"input_text": "string"}`
            *   **Response**: `{"category": "string", "reasoning": "string", "confidence_score": float, "matching_method": "string"}`
        *   `POST /api/feedback`: Submit feedback on a categorization.
            *   **Request Body**: `{"input_text": "string", "predicted_category": "string", "corrected_category": "string", "reasoning": "string", "confidence_score": float}`
        *   `POST /api/sessions`: Start a new user session.
            *   **Response**: `{"session_id": "string", ...}`
        *   `POST /api/keywords`: Add a new custom keyword.
            *   **Request Body**: `{"keyword": "string", "category": "string", "user_id": "string"}`
        *   `GET /api/keywords`: Retrieve keywords.
            *   **Query Params**: `user_id` (optional)
        *   `GET /api/categorized_expenses/{session_id}`: Get categorized expenses for a session.
        *   `GET /api/interactions/{session_id}`: Get interaction history for a session.
    *   **Explain**: These endpoints allow other applications or services to integrate with the Expense Categorizer, making it a versatile backend solution.

## 🎯 Conclusion

The Expense Categorizer provides a powerful, adaptable, and insightful solution for managing financial transactions. Its intelligent categorization, user-driven feedback loop, and analytical capabilities make it a valuable tool for personal finance management and business expense tracking.
