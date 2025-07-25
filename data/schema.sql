-- schema.sql

DROP TABLE IF EXISTS keyword_category;

CREATE TABLE keyword_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    category TEXT NOT NULL
);

DROP TABLE IF EXISTS feedback;

CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_text TEXT NOT NULL,
    predicted_category TEXT,
    corrected_category TEXT NOT NULL,
    reasoning TEXT,
    confidence_score REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS categorization_log;

CREATE TABLE categorization_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    input_text TEXT NOT NULL,
    final_category TEXT NOT NULL,
    matching_method TEXT,
    confidence_score REAL,
    tags TEXT
);

DROP TABLE IF EXISTS sessions;

CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    metadata TEXT
);

DROP TABLE IF EXISTS interactions;

CREATE TABLE interactions (
    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    interaction_type TEXT NOT NULL,
    input_data TEXT,
    output_data TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

DROP TABLE IF EXISTS categorized_expenses;

CREATE TABLE categorized_expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL,
    amount REAL,
    category TEXT NOT NULL,
    confidence_score REAL,
    raw_input TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);


