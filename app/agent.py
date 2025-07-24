import sqlite3
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from app.tools.db_matcher import KeywordDBMatcherTool
from app.tools.regex_matcher import RegexMatcherTool

# --- AgentState Definition ---
class AgentState(TypedDict):
    input_text: str
    category: Optional[str]
    reasoning: Optional[str]

# --- Tool Initialization ---
conn = sqlite3.connect("data/keywords.db", check_same_thread=False)
db_tool = KeywordDBMatcherTool(conn=conn)

category_map = {
    "Transport": ["uber", "fuel", "taxi"],
    "Food": ["groceries", "pizza", "restaurant"],
    "Housing": ["rent"],
    "Utilities": ["internet", "electricity"],
    "Communication": ["airtime", "data"],
    "Income": ["salary", "paycheck"],
    "Entertainment": ["netflix", "spotify", "youtube"]
}
regex_tool = RegexMatcherTool(category_map=category_map)

# --- Node and Router Functions ---
def db_matcher_node(state: AgentState) -> AgentState:
    print("---RUNNING DB MATCHER---")
    category = db_tool.get_best_match(state["input_text"])
    reasoning = "Matched using DB" if category else None
    print(f"DB Matcher Result: {category}")
    return {
        "input_text": state["input_text"],
        "category": category,
        "reasoning": reasoning
    }

def regex_matcher_node(state: AgentState) -> AgentState:
    print("---RUNNING REGEX MATCHER---")
    category = regex_tool.get_best_match(state["input_text"])
    reasoning = "Matched using Regex" if category else "No match found"
    print(f"Regex Matcher Result: {category}")
    return {
        "input_text": state["input_text"],
        "category": category or "Unknown",
        "reasoning": reasoning
    }

def category_router(state: AgentState) -> str:
    print("---ROUTING---")
    if state.get("category"):
        print("Category found, ending.")
        return END
    print("No category found, proceeding to regex matcher.")
    return "regex_matcher"

# --- Graph Definition ---
def build_graph():
    categorizer = StateGraph(AgentState)

    categorizer.add_node("db_matcher", db_matcher_node)
    categorizer.add_node("regex_matcher", regex_matcher_node)

    categorizer.set_entry_point("db_matcher")
    categorizer.add_conditional_edges(
        "db_matcher",
        category_router,
        {
            "regex_matcher": "regex_matcher",
            END: END
        }
    )

    categorizer.add_edge("regex_matcher", END)
    return categorizer.compile()

# Compile once globally for reuse
graph = build_graph()

# --- Main Execution Block ---
def run_categorizer(input_text: str) -> AgentState:
    input_state: AgentState = {
        "input_text": input_text,
        "category": None,
        "reasoning": None
    }
    return graph.invoke(input_state)

if __name__ == "__main__":
    test_inputs = [
        "Paid for my uber ride and groceries",
        "Monthly electricity bill",
        "Rent paid for April",
        "Data bundle recharge"
    ]

    for input_text in test_inputs:
        print("\n" + "=" * 20)
        print(f"Invoking graph with input: {input_text}")
        result = run_categorizer(input_text)
        print("---FINAL RESULT---")
        print(result)
