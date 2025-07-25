# Expense Categorizer Application

## About

This application provides an intelligent, automated solution for categorizing expenses from textual descriptions. It features a multi-stage AI agent utilizing keyword database, regex pattern matching, and an LLM fallback, accessible via a robust FastAPI.

## Features

*   **Responsive Design:** The user interface is designed to be mobile-first and responsive, providing an optimal experience on both desktop and mobile devices.
*   **Intelligent Expense Categorization:** Automatically assigns categories (e.g., Food, Transport, Housing) to expense descriptions.
*   **Multi-Stage Hybrid Matching System:**
    *   **Text Normalization:** Preprocesses input text to clean noise and standardize formats (e.g., "POS TRXN", currency symbols, dates, times, bank/card terms, common transaction verbs).
    *   **Keyword Database Matching:** Utilizes a SQLite database (`keywords.db`) for precise keyword-to-category mapping. Ideal for common, well-defined expenses.
    *   **Regex Pattern Matching:** Employs regular expressions defined in `app/config/categories.yaml` for flexible pattern-based categorization. Useful for broader categories or variations in descriptions.
    *   **LLM Fallback:** If neither DB nor Regex matching yields a confident result, an OpenAI Large Language Model is used as a fallback to categorize the expense.
*   **Confidence Scores:** Each categorization method (DB, Regex, LLM) provides a confidence score, indicating the certainty of the match.
*   **User Feedback Mechanism:** Allows users to correct miscategorizations. The system conditionally learns from these corrections (especially for low-confidence LLM predictions) by automatically adding new keywords to the database, improving future accuracy.
*   **Categorization Logging:** All categorization events are logged, including input text, final category, matching method, confidence score, and optional tags.
*   **Persistent Sessions:** Tracks user sessions, allowing for a continuous interaction history and personalized experience.
*   **Analytics Dashboard:** Provides insights into categorization patterns, user feedback, and session activity through a dedicated Streamlit analytics page.
*   **Multi-Channel Interaction:**
    *   **Telegram Bot:** Interact with the categorizer directly via Telegram messages.
    *   **SMS (Twilio):** Send expense descriptions via SMS and receive categorized results.
*   **FastAPI:** A robust RESTful API for integrating the categorization logic into other applications or services.
*   **Extensible Configuration:** Easily add or modify categories and keywords through configuration files and the SQLite database.

## Architecture

The application is structured into several key components:

1.  **Streamlit UI (`streamlit_app.py`):** A simple and intuitive web interface for interactive expense categorization and analytics. It interacts with the FastAPI backend.
2.  **FastAPI (`app/main.py`, `app/agent_api.py`, `app/telegram_api.py`, `app/sms_api.py`):** Provides API endpoints for expense categorization (`/api/categorize`), user feedback submission (`/api/feedback`), session management (`/api/sessions`), retrieving interaction/expense logs (`/api/interactions`, `/api/categorized_expenses`), and handling webhooks for Telegram and SMS.
3.  **LangGraph Agent (`app/agent.py`):** The core intelligence of the application. It defines a state graph with multiple nodes:
    *   `db_matcher`: Attempts to categorize expenses using the `KeywordDBMatcherTool`.
    *   `regex_matcher`: If `db_matcher` fails, this node uses the `RegexMatcherTool` for categorization.
    *   `llm_categorizer`: If both `db_matcher` and `regex_matcher` fail, this node uses an OpenAI Large Language Model as a fallback to categorize the expense.
    The agent intelligently routes the expense description through these matchers and determines the final category based on confidence.
4.  **Matching Tools (`app/tools/`):**
    *   `text_normalizer.py`: Implements logic for cleaning and standardizing input text.
    *   `db_matcher.py`: Implements the logic for matching expense descriptions against keywords stored in `data/keywords.db`.
    *   `regex_matcher.py`: Implements the logic for matching expense descriptions against regex patterns defined in `app/config/categories.yaml`.
5.  **Data and Configuration:**
    *   `data/keywords.db`: A SQLite database storing keyword-to-category mappings, feedback, logs, session data, interaction logs, and categorized expenses.
    *   `data/schema.sql`: Defines the schema for `keywords.db`, including tables for `keyword_category`, `feedback`, `categorization_log`, `sessions`, `interactions`, and `categorized_expenses`.
    *   `data/seed.sql`: Populates `keywords.db` with initial data.
    *   `app/config/categories.yaml`: Defines categories and associated regex patterns for the `RegexMatcherTool`.

## Setup and Installation

To get the application up and running, follow these steps:

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/expense_categorizer_agent.git
cd expense_categorizer_agent
```

### 2. Create and Activate a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: `venv\Scripts\activate`
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the Database

The application uses a SQLite database. You need to initialize it and populate it with seed data.

```bash
python init_db.py
sqlite3 data/keywords.db < data/seed.sql
```
**Note:** Ensure you have the `OPENAI_API_KEY` environment variable set for the LLM fallback to work.

## Usage

### Running the Streamlit Application

To launch the interactive Streamlit UI:

```bash
streamlit run streamlit_app.py
```

This command will open the application in your default web browser (usually at `http://localhost:8501`). You can then enter expense descriptions and see the categorized results.

### Running the FastAPI Backend

To start the FastAPI server (for API access and webhook handling):

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

#### API Endpoints

*   **POST `/api/categorize`**
    *   **Description:** Categorizes an expense description.
    *   **Request Body:**
        ```json
        {
            "input_text": "Paid for my uber ride and groceries"
        }
        ```
    *   **Response Body (Success):**
        ```json
        {
            "category": "Transport",
            "reasoning": "Matched using DB",
            "confidence_score": 1.0,
            "matching_method": "DB"
        }
        ```

*   **POST `/api/feedback`**
    *   **Description:** Submits user feedback for miscategorized expenses, which can be used to improve the system.
    *   **Request Body:**
        ```json
        {
            "input_text": "Paid for my uber ride and groceries",
            "predicted_category": "Unknown",
            "corrected_category": "Transport",
            "reasoning": "User corrected to Transport",
            "confidence_score": 0.5
        }
        ```
    *   **Response Body (Success):**
        ```json
        {
            "message": "Feedback received and stored successfully!"
        }
        ```

*   **POST `/api/sessions`**
    *   **Description:** Starts a new user session.
    *   **Request Body (Optional):**
        ```json
        {
            "user_id": "user123",
            "metadata": "some_session_data"
        }
        ```
    *   **Response Body (Success):**
        ```json
        {
            "session_id": "uuid-of-new-session",
            "start_time": "2023-10-27T10:00:00",
            "last_active_time": "2023-10-27T10:00:00",
            "user_id": "user123",
            "metadata": "some_session_data"
        }
        ```

*   **GET `/api/sessions/{session_id}`**
    *   **Description:** Retrieves details of a specific session.

*   **GET `/api/interactions/{session_id}`**
    *   **Description:** Retrieves all interactions for a given session.

*   **GET `/api/categorized_expenses/{session_id}`**
    *   **Description:** Retrieves all categorized expenses for a given session.

*   **POST `/telegram/telegram_webhook`**
    *   **Description:** Endpoint for Telegram bot webhooks. Receives updates from Telegram and processes messages.

*   **POST `/sms/sms_webhook`**
    *   **Description:** Endpoint for Twilio SMS webhooks. Receives incoming SMS messages and processes them.

You can test the API using tools like `curl`, Postman, or by visiting `http://127.0.0.1:8000/docs` for the interactive OpenAPI documentation (Swagger UI).

### Multi-Channel Setup (Telegram & SMS)

To enable Telegram bot and Twilio SMS interactions, you need to configure environment variables and webhooks.

1.  **Environment Variables:**
    Create or update your `.env` file in the project root with your credentials:
    ```
    TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
    TWILIO_ACCOUNT_SID="YOUR_TWILIO_ACCOUNT_SID"
    TWILIO_AUTH_TOKEN="YOUR_TWILIO_AUTH_TOKEN"
    TWILIO_PHONE_NUMBER="YOUR_TWILIO_PHONE_NUMBER"
    ```

2.  **Expose your FastAPI app publicly:**
    If running locally, use a tunneling service like `ngrok` to expose your FastAPI server (default port 8000) to the internet.
    ```bash
    ngrok http 8000
    ```
    Copy the public URL provided by ngrok (e.g., `https://your-ngrok-url.ngrok.io`).

3.  **Set up Webhooks:**
    *   **Telegram:** Make a GET request to set the webhook. Replace placeholders with your actual token and public URL:
        ```bash
        curl "https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook?url=<YOUR_PUBLIC_URL>/telegram/telegram_webhook"
        ```
    *   **Twilio:** In your Twilio Console, configure your Twilio Phone Number's "Messaging" section to point to `https://<YOUR_PUBLIC_URL>/sms/sms_webhook` for "A Message Comes In".

## Configuration and Extensibility

### Adding/Modifying Categories and Keywords

#### 1. Keyword Database (`data/keywords.db`)

For precise keyword matching, you can add or modify entries directly in the `keyword_category` table of `data/keywords.db`.

You can use a SQLite client (like `sqlite3` from the command line or a GUI tool) to manage this database.

Example of adding a new keyword:

```sql
INSERT INTO keyword_category (keyword, category) VALUES ("coffee shop", "Food");
```

#### 2. Regex Patterns (`app/config/categories.yaml`)

For pattern-based matching, edit the `app/config/categories.yaml` file. This YAML file maps categories to lists of keywords/phrases that will be used to construct regex patterns.

Example:

```yaml
Food:
  - "mcdonalds"
  - "uber eats"
  - "kfc"
Transport:
  - "uber"
  - "lyft"
  - "bolt"
Entertainment:
  - "netflix"
  - "spotify"
  - "youtube"
NewCategory:
  - "new keyword 1"
  - "new keyword 2"
```

After modifying `categories.yaml`, restart the application (FastAPI) for changes to take effect.

## Project Structure

```
.
├── .gitignore
├── Improvement Plan.md
├── README.md
├── requirements.txt
├── TODO.md
├── init_db.py            # Script to initialize the SQLite database schema
├── app/
│   ├── __init__.py
│   ├── agent_api.py      # FastAPI router for agent and feedback
│   ├── agent.py          # LangGraph agent definition
│   ├── main.py           # FastAPI application entry point
│   ├── models.py         # Pydantic models for API requests/responses
│   ├── telegram_api.py   # FastAPI router for Telegram bot webhooks
│   ├── sms_api.py        # FastAPI router for Twilio SMS webhooks
│   ├── config/
│   │   ├── __init__.py
│   │   ├── categories.yaml # Regex patterns configuration
│   │   └── settings.py   # (Potentially for future application settings)
│   ├── schema/
│   │   ├── __init__.py
│   │   └── state.py      # LangGraph agent state definition
│   └── tools/
│       ├── __init__.py
│       ├── db_matcher.py   # Keyword database matching logic
│       ├── regex_matcher.py # Regex matching logic
│       └── text_normalizer.py # Text normalization logic
├── data/
│   ├── keywords.db       # SQLite database for keyword matching, feedback, logs, and embeddings
│   ├── schema.sql        # Database schema
│   └── seed.sql          # Initial database data
├── scripts/
│   └── generate_embeddings.py # Script to generate keyword embeddings
└── tests/                # Unit and integration tests
```