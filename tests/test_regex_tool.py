from app.tools.regex_matcher import RegexMatcherTool
from app.config.settings import CategoryKeywordLoader

def setup_tool():
    loader = CategoryKeywordLoader("tests/test_categories.yaml")
    category_map = loader.load()
    return RegexMatcherTool(category_map=category_map)

# ---------- Test: run() method ----------

def test_run_exact_match():
    tool = setup_tool()
    assert tool._run("some text with keyword1") == "Test Category 1"

def test_run_no_match():
    tool = setup_tool()
    assert tool._run("Unrecognized Vendor") is None

# ---------- Test: get_all_matches() method ----------

def test_all_matches_multiple_categories():
    tool = setup_tool()
    text = "some text with keyword1 and keyword3"
    matches = tool.get_all_matches(text)
    expected = {
        "Test Category 1": ["keyword1"],
        "Test Category 2": ["keyword3"]
    }
    assert matches == expected

def test_all_matches_none():
    tool = setup_tool()
    assert tool.get_all_matches("Unknown string") == {}

# ---------- Test: get_best_match() method ----------

def test_best_match_highest_keyword_count():
    tool = setup_tool()
    text = "text with keyword1 and keyword2"
    best = tool.get_best_match(text)
    assert best == "Test Category 1"  # 2 Test Category 1 matches, 0 Test Category 2 matches

def test_best_match_tie():
    tool = setup_tool()
    text = "text with keyword1 and keyword3"
    best = tool.get_best_match(text)
    assert best in ["Test Category 1", "Test Category 2"]  # Tie: 1 match each

def test_best_match_no_match():
    tool = setup_tool()
    assert tool.get_best_match("Not a match at all") is None
