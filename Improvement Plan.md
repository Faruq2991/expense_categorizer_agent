# Improvement Plan for Expense Categorizer Agent

This document outlines detailed implementation plans for each enhancement listed in `TODO.md`, aiming to transform the Expense Categorizer Agent into a more robust and production-ready application.

---

## 🔍 1. Multi-Signal Categorization

**Goal:** Enhance categorization accuracy and robustness by combining multiple signal sources and providing confidence scores.

### Detailed Plan:

1.  **Add LLM Fallback:**
    *   **Identify LLM Integration:** Utilize `langchain-openai` (as it's already a dependency) for LLM integration.
    *   **Create LLM Tool/Node:** Develop a new LangGraph node (`llm_categorizer_node`) that takes the `input_text` and attempts to categorize it using a pre-defined LLM prompt. The prompt should guide the LLM to output a category from a predefined list (e.g., from `categories.yaml` or a combined list of all known categories).
    *   **Integrate into LangGraph:** Modify `app/agent.py`:
        *   Add the `llm_categorizer_node` to the graph.
        *   Update `category_router` to route to `llm_categorizer_node` if both `db_matcher` and `regex_matcher` return `None` or "Unknown" category.
        *   Ensure the LLM output is parsed and assigned to `state["category"]` and `state["reasoning"]`.
    *   **Error Handling:** Implement robust error handling for LLM calls (e.g., timeouts, API errors).

2.  **Combine Multiple Signal Sources (Future Iteration):**
    *   **Scoring Mechanism:** Develop a scoring system for each categorization method (DB, Regex, LLM, and later, Vector Similarity).
    *   **Confidence Scores:** Each matcher (DB, Regex, LLM) should return a confidence score along with the category. For DB/Regex, this could be binary (1.0 if matched, 0.0 if not). For LLM, it could be derived from log probabilities or a self-assessed confidence.
    *   **Voting/Ensemble:** Implement a final "decision" node in LangGraph that takes inputs from all signal sources and their confidence scores, then determines the final category based on a voting mechanism or a weighted average.

3.  **Include Confidence Scores in Output:**
    *   Modify `AgentState` to include a `confidence_score: Optional[float]`.
    *   Update `app/agent.py` and `app/agent_api.py` to return this score in the `CategorizeResponse`.
    *   Update `app/streamlit_app.py` to display the confidence score.

---

## 🧠 2. User Feedback + Learning Loop

**Goal:** Enable continuous improvement of the categorization model through user corrections.

### Detailed Plan:

1.  **Implement Feedback Mechanism in UI:**
    *   **Streamlit UI:** Add a "Correct Category" button or dropdown in `app/streamlit_app.py` that allows users to select the correct category if the initial categorization is wrong.
    *   **FastAPI Endpoint:** Create a new FastAPI endpoint (e.g., `/api/feedback`) to receive user corrections. This endpoint should accept the original `input_text`, the proposed `category`, and the `corrected_category`.
2.  **Store Feedback:**
    *   **Database Schema:** Create a new table in `data/keywords.db` (or a new SQLite database) to store feedback data (e.g., `feedback_id`, `input_text`, `predicted_category`, `corrected_category`, `timestamp`, `matching_method_used`).
    *   **Persistence:** Implement logic to write feedback to this database.
3.  **Learning Loop (Future Iteration):**
    *   **Automated Updates:** Develop a background process or a scheduled task that periodically analyzes the feedback data.
    *   **Keyword DB Update:** If a specific keyword is consistently miscategorized, automatically add or update its entry in `data/keywords.db`.
    *   **ML Model Training:** For more advanced scenarios, use the feedback data to fine-tune a lightweight ML model (e.g., a simple text classifier) that can learn from user corrections.

---

## 💾 3. Persistent Sessions + Analytics

**Goal:** Log categorization history and provide analytical insights.

### Detailed Plan:

1.  **Log Categorization Data:**
    *   **Database Schema:** Create a new table in `data/keywords.db` (or a new SQLite database) to log each categorization event. Fields should include: `log_id`, `timestamp`, `description`, `final_category`, `matching_method_used`, `confidence_score` (if implemented).
    *   **Logging Logic:** Integrate logging into `app/agent.py` (or a dedicated logging service) to record details after each `graph.invoke` call.
2.  **Visualize Analytics (Streamlit):**
    *   **New Streamlit Page:** Create a separate page or section in `app/streamlit_app.py` for analytics.
    *   **Data Retrieval:** Implement functions to query the logging database.
    *   **Visualization:** Use Streamlit's charting capabilities (`st.bar_chart`, `st.line_chart`, etc.) to display:
        *   Most common categories (bar chart).
        *   Categorization trends over time.
        *   Breakdown of matching methods used (pie chart).
        *   (If feedback implemented) Frequent keyword misses, user correction patterns.
3.  **Tagging/Grouping (Future Iteration):**
    *   **UI Element:** Add an input field in the Streamlit UI for users to add tags (e.g., "personal", "business") to transactions.
    *   **Database Field:** Add a `tags` column to the logging table.

---

## 💬 4. Natural Input Support

**Goal:** Improve the agent's ability to handle diverse and noisy real-world expense descriptions.

### Detailed Plan:

1.  **Preprocessing Pipeline:**
    *   **Text Normalization:** Create a `text_normalizer.py` module in `app/tools/` (or a new `app/preprocessing/` directory).
    *   **Cleaning Functions:** Implement functions for:
        *   Removing common noise (e.g., "POS TRXN", "USD", currency symbols).
        *   Handling abbreviations (e.g., "Momo" -> "Mobile Money").
        *   Lowercasing and removing extra whitespace.
        *   Stemming/Lemmatization (optional, for more advanced matching).
    *   **Integration:** Apply this preprocessing pipeline to the `input_text` before it enters the `db_matcher` or `regex_matcher` nodes in `app/agent.py`.
2.  **Expand Regex/Keyword Coverage:**
    *   Continuously update `data/seed.sql` and `app/config/categories.yaml` with more real-world examples of noisy or abbreviated descriptions.

---

## 📚 5. Hybrid Matching (Regex + Embeddings)

**Goal:** Introduce semantic understanding to categorization using vector embeddings.

### Detailed Plan:

1.  **Embed Keywords:**
    *   **Embedding Model:** Choose a suitable sentence embedding model (e.g., `sentence-transformers` or OpenAI embeddings).
    *   **Pre-compute Embeddings:** For all keywords in `data/keywords.db` and phrases in `app/config/categories.yaml`, compute their embeddings.
    *   **Store Embeddings:** Store these embeddings in a new table in `data/keywords.db` or a dedicated vector store (e.g., FAISS, ChromaDB).
2.  **Vector Similarity Matching Tool:**
    *   **New Tool:** Create a `vector_matcher.py` in `app/tools/`.
    *   **Matching Logic:** This tool will take the `input_text`, compute its embedding, and then find the most similar keyword embedding from the stored embeddings.
    *   **Thresholding:** Implement a similarity threshold to determine if a match is confident enough.
3.  **Integrate into LangGraph:**
    *   **New Node:** Add a `vector_matcher_node` to `app/agent.py`.
    *   **Routing:** Integrate this node into the `category_router` or a new ensemble node, potentially as another fallback or as a parallel signal source.
4.  **Merge Results:**
    *   Develop a strategy to combine results from regex, DB, and vector similarity (e.g., weighted voting, hierarchical fallback).

---

## 🌍 6. Multi-language Support

**Goal:** Enable the application to categorize expenses in multiple languages.

### Detailed Plan:

1.  **Localized Keyword Mappings:**
    *   **Configuration Structure:** Modify `app/config/categories.yaml` or create new YAML files (e.g., `categories_es.yaml`, `categories_fr.yaml`) to store language-specific keywords and regex patterns.
    *   **Database Extension:** Add a `language` column to the `keyword_category` table in `data/keywords.db` to support language-specific keywords.
2.  **Language Detection (Optional but Recommended):**
    *   Integrate a language detection library (e.g., `langdetect`) to automatically identify the language of the `input_text`.
3.  **Dynamic Tool Loading:**
    *   Modify `app/agent.py` to dynamically load the correct `category_map` and query the `db_tool` based on the detected (or user-selected) language.
4.  **Translation APIs (Fallback):**
    *   For languages not explicitly supported by localized mappings, integrate a translation API (e.g., Google Translate API) to translate the `input_text` to a supported language before categorization.

---

## 🧪 7. Testing & Monitoring

**Goal:** Ensure the accuracy, reliability, and performance of the categorization system.

### Detailed Plan:

1.  **Matching Coverage Tracking:**
    *   **Logging:** Enhance the logging (from "Persistent Sessions" plan) to record which specific keyword/regex pattern was matched, or if no match occurred.
    *   **Reporting:** Generate reports (e.g., via Streamlit analytics) showing the coverage of existing patterns and identifying frequently unmatched descriptions.
2.  **Automated Monitoring:**
    *   **Metrics:** Define key metrics:
        *   Categorization accuracy (requires ground truth/feedback).
        *   Unmatched rate.
        *   Fallback rate (how often LLM/vector matching is used).
        *   Latency of categorization.
    *   **Alerting:** Set up alerts for significant drops in accuracy or increases in unmatched rates.
3.  **Evaluation Framework:**
    *   **Test Datasets:** Create diverse test datasets with known `input_text` and `expected_category` pairs.
    *   **Automated Tests:** Develop comprehensive unit and integration tests (`tests/`) to evaluate precision, recall, and F1-score for each matching method and the overall system.
    *   **Regression Testing:** Ensure that new features or updates do not degrade existing categorization performance.

---

## 📱 8. Mobile-First UX

**Goal:** Optimize the user experience for mobile devices and explore alternative interaction channels.

### Detailed Plan:

1.  **Responsive Web Interface:**
    *   **Streamlit Styling:** Utilize Streamlit's theming capabilities and custom CSS to ensure the `streamlit_app.py` is fully responsive and looks good on various screen sizes.
    *   **Mobile-First Design:** Prioritize mobile layouts during UI development.
2.  **Progressive Web App (PWA) (Future Iteration):**
    *   **Manifest File:** Create a `manifest.json` file.
    *   **Service Worker:** Implement a service worker for offline capabilities and faster loading.
3.  **Chatbot Integrations (Future Iteration):**
    *   **API Integration:** Leverage the FastAPI endpoint to integrate with messaging platforms.
    *   **Platform-Specific Bots:** Develop simple bots for WhatsApp, Telegram, or SMS that can send expense descriptions to the API and return categorized results.

---

## 🔌 9. Real-Time Integrations

**Goal:** Enable seamless data ingestion from external sources and export to accounting platforms.

### Detailed Plan:

1.  **Data Ingestion (Future Iteration):**
    *   **Email/SMS Parsing:** Develop modules to parse expense details from bank email alerts or SMS messages. This will likely involve advanced regex or NLP techniques.
    *   **API Webhooks:** Explore if bank APIs or mobile money services offer webhooks for real-time transaction notifications.
2.  **Data Export:**
    *   **Google Sheets/Excel:** Implement functions to export categorized data to CSV or directly to Google Sheets/Excel via their respective APIs.
    *   **Accounting Platform APIs:** Research and integrate with APIs of popular accounting platforms (QuickBooks, Wave, Notion) to push categorized transactions. This will require understanding their data models and authentication mechanisms.

---

## 🧭 10. Custom Category Profiles

**Goal:** Provide users with the flexibility to define and manage their own categorization rules.

### Detailed Plan:

1.  **User-Specific Category Mappings:**
    *   **Database Schema:** Extend `data/keywords.db` (or create a new database) to include a `user_id` column in the `keyword_category` table, allowing for user-specific keyword mappings.
    *   **UI for Management:** Develop a Streamlit UI page where users can:
        *   View their custom categories.
        *   Add new custom categories.
        *   Add/remove keywords for their custom categories.
        *   Override default categories for specific keywords.
2.  **Sub-categories and Nested Types (Future Iteration):**
    *   **Hierarchical Structure:** Modify the category data model to support parent-child relationships for categories.
    *   **UI for Hierarchy:** Update the Streamlit UI to allow users to define and visualize sub-categories.
3.  **Category Splitting (Future Iteration):**
    *   **UI Input:** Provide a mechanism in the Streamlit UI for users to specify percentage splits for an expense across multiple categories.
    *   **Logging:** Ensure the logging system can record these split categorizations.
    *   **Reporting:** Update analytics to reflect split expenses accurately.
