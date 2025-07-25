import sqlite3
import os

# Define the path to the database file
# This ensures the script always finds the DB in the 'data' subfolder
DB_FOLDER = 'data'
DB_NAME = 'keywords.db'
DB_PATH = os.path.join(DB_FOLDER, DB_NAME)

def initialize_database():
    """
    Initializes the SQLite database by creating necessary tables if they don't exist.
    This function is safe to run multiple times.
    """
    print(f"Ensuring database exists at: {DB_PATH}")

    # Create the 'data' directory if it doesn't exist
    os.makedirs(DB_FOLDER, exist_ok=True)

    # Connect to the SQLite database (this will create the file if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- Create categorization_log table ---
    # This is the table that your agent_api.py is trying to write to.
    print("Creating 'categorization_log' table if it doesn't exist...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorization_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            input_text TEXT NOT NULL,
            final_category TEXT NOT NULL,
            matching_method TEXT,
            confidence_score REAL,
            tags TEXT
        )
    """)
    print("'categorization_log' table is ready.")

    # --- Create keyword_category table (optional but good practice) ---
    # Also ensure the table for your KeywordDBMatcherTool exists.
    print("Creating 'keyword_category' table if it doesn't exist...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keyword_category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)
    print("'keyword_category' table is ready.")

    # --- Create sessions table ---
    print("Creating 'sessions' table if it doesn't exist...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_active_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            metadata TEXT
        )
    """)
    print("'sessions' table is ready.")

    # --- Create interactions table ---
    print("Creating 'interactions' table if it doesn't exist...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            interaction_type TEXT NOT NULL,
            input_data TEXT,
            output_data TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    print("'interactions' table is ready.")

    # --- Create categorized_expenses table ---
    print("Creating 'categorized_expenses' table if it doesn't exist...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorized_expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT NOT NULL,
            amount REAL,
            category TEXT NOT NULL,
            confidence_score REAL,
            raw_input TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    print("'categorized_expenses' table is ready.")

    # You could add some default keywords here if you wanted, for example:
    # try:
    #     cursor.execute("INSERT INTO keyword_category (keyword, category) VALUES (?, ?)", ("uber", "Transport"))
    # except sqlite3.IntegrityError:
    #     print("'uber' keyword already exists.") # Ignore if it's already there
    

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("\nDatabase initialization complete.")

if __name__ == "__main__":
    initialize_database()

