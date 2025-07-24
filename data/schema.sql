-- schema.sql

DROP TABLE IF EXISTS keyword_category;

CREATE TABLE keyword_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    category TEXT NOT NULL
);
