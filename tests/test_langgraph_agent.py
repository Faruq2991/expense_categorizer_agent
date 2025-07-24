import pytest
import sqlite3
from app.agent import build_graph
from app.tools.db_matcher import KeywordDBMatcherTool
from app.tools.regex_matcher import RegexMatcherTool

# --- Test Setup using Pytest Fixtures ---

@pytest.fixture
def setup_database():
    """
    Creates a fresh, in-memory SQLite database for each test.
    This fixture ensures that tests are isolated and don't interfere with each other
    or depend on a persistent db file.
    """
    conn = sqlite3.connect(":memory:")  # Use in-memory database
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE keyword_category (
            keyword TEXT PRIMARY KEY,
            category TEXT NOT NULL
        )
    """)
    # Add ONLY the data needed for the DB match test
    cursor.execute("INSERT INTO keyword_category (keyword, category) VALUES (?, ?)", ("uber", "Transport"))
    conn.commit()
    yield conn  # Provide the connection to the test
    conn.close() # Teardown: close the connection after the test is done

@pytest.fixture
def configured_graph(setup_database):
    """
    Builds the graph using the isolated, in-memory database from setup_database.
    This ensures the graph used in tests has a known, controlled state.
    """
    # Override the build_graph function to use our test-specific tools
    # This is a key pattern for testing complex applications.
    
    # 1. Re-create the tools with the in-memory DB connection
    db_tool = KeywordDBMatcherTool(conn=setup_database)
    
    category_map = {
        "Transport": ["uber", "fuel", "taxi"],
        "Food": ["groceries", "pizza", "restaurant"],
        "Housing": ["rent"],
        "Utilities": ["internet", "electricity"], # This is for the regex fallback
        "Communication": ["airtime", "data"],
        "Income": ["salary", "paycheck"]
    }
    regex_tool = RegexMatcherTool(category_map=category_map)

    # 2. Re-implement the build_graph logic here for clarity and isolation
    # We are now injecting our test-specific tools.
    from langgraph.graph import StateGraph, END
    from app.agent import AgentState, db_matcher_node, regex_matcher_node, category_router

    # This is a bit of a workaround to inject the test tools into the nodes
    # A more advanced setup might use dependency injection frameworks.
    def test_db_node(state):
        category = db_tool.get_best_match(state["input_text"])
        return {"category": category, "reasoning": "Matched using DB" if category else None}

    def test_regex_node(state):
        category = regex_tool.get_best_match(state["input_text"])
        return {"category": category or "Unknown", "reasoning": "Matched using Regex" if category else "No match found"}

    categorizer = StateGraph(AgentState)
    categorizer.add_node("db_matcher", test_db_node)
    categorizer.add_node("regex_matcher", test_regex_node)
    categorizer.set_entry_point("db_matcher")
    categorizer.add_conditional_edges("db_matcher", category_router, {"regex_matcher": "regex_matcher", END: END})
    categorizer.add_edge("regex_matcher", END)
    
    return categorizer.compile()


# --- Corrected Tests ---

def test_db_match_found(configured_graph):
    """
    Tests the case where a keyword IS found in the database.
    The database for this test only contains 'uber'.
    """
    graph = configured_graph
    state = {"input_text": "Uber payment"}
    result = graph.invoke(state)
    assert result["category"] == "Transport"
    assert result["reasoning"] == "Matched using DB"

def test_db_miss_regex_match(configured_graph):
    """
    Tests the case where the keyword is NOT in the DB but IS in the regex map.
    The database for this test does NOT contain 'electricity'.
    """
    graph = configured_graph
    state = {"input_text": "electricity bill"}
    result = graph.invoke(state)
    assert result["category"] == "Utilities"
    assert result["reasoning"] == "Matched using Regex"

def test_db_miss_regex_miss(configured_graph):
    """
    Tests the case where the keyword is in neither the DB nor the regex map.
    """
    graph = configured_graph
    state = {"input_text": "random nonsense transaction"}
    result = graph.invoke(state)
    assert result["category"] == "Unknown"
    assert result["reasoning"] == "No match found"

