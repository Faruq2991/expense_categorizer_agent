import sqlite3
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from app.tools.db_matcher import KeywordDBMatcherTool
from app.tools.regex_matcher import RegexMatcherTool

# --- AgentState Definition ---
class AgentState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        input_text: The transaction description to categorize.
        category: The determined category for the transaction.
        reasoning: Explanation of how the category was determined.
    """
    input_text: str
    category: Optional[str]
    reasoning: Optional[str]


# --- Tool Initialization ---
conn = sqlite3.connect("data/keywords.db")
db_tool = KeywordDBMatcherTool(conn=conn)

category_map = {
    "Transport": ["uber", "fuel", "taxi"],
    "Food": ["groceries", "pizza", "restaurant"],
    "Housing": ["rent"],
    "Utilities": ["internet", "electricity"],
    "Communication": ["airtime", "data"],
    "Income": ["salary", "paycheck"]
}

regex_tool = RegexMatcherTool(category_map=category_map)


# --- Node and Router Functions ---
def db_matcher_node(state: AgentState) -> AgentState:
    """
    Uses the database tool to find the best category match.
    """
    print("---RUNNING DB MATCHER---")
    category = db_tool.get_best_match(state["input_text"])
    reasoning = "Matched using DB" if category else None
    print(f"DB Matcher Result: {category}")
    return {
        "category": category,
        "reasoning": reasoning
    }

def regex_matcher_node(state: AgentState) -> AgentState:
    """
    Uses the regex tool to find the best category match as a fallback.
    """
    print("---RUNNING REGEX MATCHER---")
    category = regex_tool.get_best_match(state["input_text"])
    reasoning = "Matched using Regex" if category else "No match found"
    print(f"Regex Matcher Result: {category}")
    return {
        "category": category or "Unknown",
        "reasoning": reasoning
    }

def category_router(state: AgentState) -> str:
    """
    Determines the next step based on whether a category was found.
    """
    print("---ROUTING---")
    if state.get("category"):
        print("Category found, ending.")
        return END
    print("No category found, proceeding to regex matcher.")
    return "regex_matcher"


# --- Graph Definition ---

def build_graph():
    """
    Builds and compiles the LangGraph state machine.
    """
    categorizer = StateGraph(AgentState)

    # Add the nodes to the graph
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

# --- Main Execution Block ---

if __name__ == "__main__":
    def run_categorizer(input_text: str) -> dict:
        graph = build_graph()  # From your existing code
        input_state = {"input_text": input_text}
        result = graph.invoke(input_state)
        return result
    # Build the graph
    graph = build_graph()

    # Define an initial state to run the graph with
    input_state = {
        "input_text": "Paid for my uber ride and groceries",
    }

    print("Invoking graph with input:", input_state)
    
    # The graph's .invoke method automatically populates the AgentState
    result = graph.invoke(input_state)

    print("\n---FINAL RESULT---")
    print(result)

    # Example of no DB match
    print("\n" + "="*20 + "\n")
    input_state_no_db_match = {
        "input_text": "Monthly electricity bill"
    }
    print("Invoking graph with input:", input_state_no_db_match)
    result_no_match = graph.invoke(input_state_no_db_match)
    print("\n---FINAL RESULT---")
    print(result_no_match)
