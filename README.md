# Expense Categorizer Application

## About

This application provides an intelligent, automated solution for categorizing expenses from textual descriptions. It features a multi-stage AI agent utilizing both keyword database and regex pattern matching, accessible via a user-friendly Streamlit interface and a robust FastAPI.

## Features

*   **Intelligent Expense Categorization:** Automatically assigns categories (e.g., Food, Transport, Housing) to expense descriptions.
*   **Hybrid Matching System:**
    *   **Keyword Database Matching:** Utilizes a SQLite database (`keywords.db`) for precise keyword-to-category mapping. Ideal for common, well-defined expenses.
    *   **Regex Pattern Matching:** Employs regular expressions defined in `app/config/categories.yaml` for flexible pattern-based categorization. Useful for broader categories or variations in descriptions.
*   **LangGraph Agent Orchestration:** A sophisticated agent orchestrates the categorization process, first attempting a database match and falling back to regex matching if no direct keyword match is found.
*   **Streamlit User Interface:** A simple and intuitive web interface for interactive expense categorization.
*   **FastAPI:** A RESTful API endpoint for integrating the categorization logic into other applications or services.
*   **Extensible Configuration:** Easily add or modify categories and keywords through configuration files and the SQLite database.

## Architecture

The application is structured into several key components:

1.  **Streamlit UI (`app/streamlit_app.py`):** The frontend interface that allows users to input expense descriptions and view categorization results. It interacts directly with the LangGraph agent.
2.  **FastAPI (`app/main.py`, `app/agent_api.py`):** Provides a `/api/categorize` endpoint for external systems to submit expense descriptions and receive categorized results.
3.  **LangGraph Agent (`app/agent.py`):** The core intelligence of the application. It defines a state graph with two main nodes:
    *   `db_matcher`: Attempts to categorize expenses using the `KeywordDBMatcherTool`.
    *   `regex_matcher`: If `db_matcher` fails, this node uses the `RegexMatcherTool` for categorization.
    The agent intelligently routes the expense description through these matchers.
4.  **Matching Tools (`app/tools/`):**
    *   `db_matcher.py`: Implements the logic for matching expense descriptions against keywords stored in `data/keywords.db`.
    *   `regex_matcher.py`: Implements the logic for matching expense descriptions against regex patterns defined in `app/config/categories.yaml`.
5.  **Data and Configuration:**
    *   `data/keywords.db`: A SQLite database storing keyword-to-category mappings.
    *   `data/schema.sql`: Defines the schema for `keywords.db`.
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

The application uses a SQLite database for keyword matching. You need to initialize it and populate it with seed data.

```bash
sqlite3 data/keywords.db < data/schema.sql
sqlite3 data/keywords.db < data/seed.sql
```

## Usage

### Running the Streamlit Application

To launch the interactive Streamlit UI:

```bash
streamlit run app/streamlit_app.py
```

This command will open the application in your default web browser (usually at `http://localhost:8501`). You can then enter expense descriptions and see the categorized results.

### Running the FastAPI

To start the FastAPI server (for API access):

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

#### API Endpoint

*   **POST `/api/categorize`**
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
            "reasoning": "Matched using DB"
        }
        ```
    *   **Response Body (No Match):**
        ```json
        {
            "category": "Unknown",
            "reasoning": "No match found"
        }
        ```

You can test the API using tools like `curl`, Postman, or by visiting `http://127.0.0.1:8000/docs` for the interactive OpenAPI documentation (Swagger UI).

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

After modifying `categories.yaml`, restart the application (both Streamlit and FastAPI) for changes to take effect.

## Project Structure

```
.
├── .gitignore
├── requirements.txt
├── api/                  # (Potentially for future external API definitions)
├── app/
│   ├── __init__.py
│   ├── agent_api.py      # FastAPI router for agent
│   ├── agent.py          # LangGraph agent definition
│   ├── main.py           # FastAPI application entry point
│   ├── models.py         # Pydantic models for API requests/responses
│   ├── README.md         # (This file)
│   ├── streamlit_app.py  # Streamlit UI application
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
│       └── regex_matcher.py # Regex matching logic
├── data/
│   ├── keywords.db       # SQLite database for keyword matching
│   ├── schema.sql        # Database schema
│   └── seed.sql          # Initial database data
└── tests/                # Unit and integration tests
```
