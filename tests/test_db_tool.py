import os
import sqlite3
import pytest
from app.tools.db_matcher import KeywordDBMatcherTool

# Setup: create in-memory DB for isolated tests
@pytest.fixture(scope="function")
def test_db():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS keyword_category;")
    
    cursor.execute("DROP TABLE IF EXISTS keyword_category;")
    cursor.execute("CREATE TABLE keyword_category (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, keyword TEXT NOT NULL, category TEXT NOT NULL, UNIQUE(user_id, keyword));")

    # Insert test data
    seed_data = [
        (None, "uber", "Transport"),
        (None, "fuel", "Transport"),
        (None, "groceries", "Food"),
        (None, "pizza", "Food"),
        (None, "rent", "Housing"),
        (None, "internet", "Utilities"),
        (None, "airtime", "Communication"),
        (None, "salary", "Income")
    ]

    cursor.executemany("INSERT INTO keyword_category (user_id, keyword, category) VALUES (?, ?, ?)", seed_data)
    conn.commit()

    yield conn

    # Teardown
    conn.close()

# Initialize tool with test DB connection
@pytest.fixture
def matcher_tool(test_db):
    return KeywordDBMatcherTool(conn=test_db)

# --- Test cases ---

def test_match_single_keyword(matcher_tool):
    assert matcher_tool.get_best_match("Just paid for Uber ride") == "Transport"

def test_match_another_category(matcher_tool):
    assert matcher_tool.get_best_match("Monthly rent was paid") == "Housing"

def test_case_insensitive_matching(matcher_tool):
    assert matcher_tool.get_best_match("Groceries and Pizza") == "Food"

def test_multiple_matches_returns_most_relevant(matcher_tool):
    # "groceries" and "pizza" are both in Food category
    assert matcher_tool.get_best_match("groceries, pizza and airtime") == "Food"

def test_no_match_returns_none(matcher_tool):
    assert matcher_tool.get_best_match("Went hiking and camping") is None
