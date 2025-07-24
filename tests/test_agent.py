import pytest
from app.agent import run_categorizer

@pytest.mark.parametrize("input_text, expected_category", [
    ("Bought pizza at Domino's", "Food"),
    ("Paid for Uber ride", "Transport"),
    ("Monthly Netflix subscription", "Entertainment"),
    ("Unknown input text", "Unknown"),
])
def test_agent_categorization(input_text, expected_category):
    result = run_categorizer(input_text)
    assert isinstance(result, dict)
    assert "category" in result
    assert "reasoning" in result

    assert result["category"] == expected_category
