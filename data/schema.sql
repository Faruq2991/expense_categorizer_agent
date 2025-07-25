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

DROP TABLE IF EXISTS keyword_embeddings;

CREATE TABLE keyword_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    embedding BLOB NOT NULL
);
