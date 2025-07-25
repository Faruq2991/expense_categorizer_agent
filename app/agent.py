import sqlite3
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import yaml
import os
from dotenv import load_dotenv

# --- Local Imports ---
# Ensure these tools are in the specified paths
from app.tools.db_matcher import KeywordDBMatcherTool
from app.tools.regex_matcher import RegexMatcherTool
from app.tools.text_normalizer import normalize_text

# --- Environment Setup ---
# Load environment variables from a .env file (for OPENAI_API_KEY)
load_dotenv()

# --- AgentState Definition ---
class AgentState(TypedDict):
    """
    Represents the state of our graph. It's the shared memory between nodes.
    
    Attributes:
        input_text: The normalized transaction description.
        user_id: The ID of the user making the request (optional).
        category: The final determined category.
        reasoning: Explanation of the matching method.
        confidence_score: A score indicating the certainty of the match.
    """
    input_text: str
    user_id: Optional[str]
    category: Optional[str]
    reasoning: Optional[str]
    confidence_score: Optional[float]


# --- Tool and LLM Initialization ---

def initialize_llm_and_regex_tool():
    """Initializes and returns the LLM chain and Regex Tool."""
    # Regex Tool
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'categories.yaml')
        with open(config_path, 'r') as f:
            category_map = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: categories.yaml not found at {config_path}. Please ensure it exists.")
        category_map = {}
    regex_tool = RegexMatcherTool(category_map=category_map)

    # LLM Chain
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) # Automatically uses OPENAI_API_KEY from .env
    categories_list = list(category_map.keys()) + ["Unknown"]
    
    llm_prompt = PromptTemplate.from_template(
        """You are an expert expense categorization assistant.
        Your task is to categorize the given expense description into one of the following categories: {categories}.
        Respond with only the category name and nothing else. If none of the categories seem to fit, respond with "Unknown".

        Expense Description: "{expense_description}"
        Category:"""
    )
    llm_chain = llm_prompt | llm | StrOutputParser()
    return regex_tool, llm_chain, categories_list

# Initialize tools globally so they are created only once
regex_tool, llm_chain, CATEGORIES = initialize_llm_and_regex_tool()


# --- Node and Router Functions ---

def db_matcher_node(state: AgentState) -> dict:
    """
    Attempts to categorize using the high-confidence database tool.
    Initializes db_tool with user_id from state.
    """
    print("---1. DB MATCHER---")
    conn = sqlite3.connect("data/keywords.db", check_same_thread=False)
    db_tool = KeywordDBMatcherTool(conn=conn, user_id=state.get("user_id"))
    category = db_tool.get_best_match(state["input_text"])
    conn.close() # Close connection after use
    if category:
        print(f"Result: Found category '{category}'")
        return {
            "category": category,
            "reasoning": "Matched using DB",
            "confidence_score": 1.0
        }
    print("Result: No match found.")
    return {}

def regex_matcher_node(state: AgentState) -> dict:
    """Attempts to categorize using the medium-confidence regex tool."""
    print("---2. REGEX MATCHER---")
    category = regex_tool.get_best_match(state["input_text"])
    if category:
        print(f"Result: Found category '{category}'")
        return {
            "category": category,
            "reasoning": "Matched using Regex",
            "confidence_score": 0.8
        }
    print("Result: No match found.")
    return {}

def llm_categorizer_node(state: AgentState) -> dict:
    """Fallback to LLM for categorization."""
    print("---3. LLM CATEGORIZER---")
    try:
        llm_category = llm_chain.invoke({
            "expense_description": state["input_text"],
            "categories": ", ".join(CATEGORIES)
        })
        
        if llm_category in CATEGORIES:
            print(f"Result: Found category '{llm_category}'")
            return {
                "category": llm_category,
                "reasoning": "Matched using LLM",
                "confidence_score": 0.6 if llm_category != "Unknown" else 0.0
            }
        else:
            print(f"Result: LLM returned an invalid category ('{llm_category}'). Defaulting to Unknown.")
            return {"category": "Unknown", "reasoning": f"LLM returned invalid category: {llm_category}", "confidence_score": 0.0}
    except Exception as e:
        print(f"Error during LLM categorization: {e}")
        return {"category": "Unknown", "reasoning": "LLM categorization failed", "confidence_score": 0.0}

def router(state: AgentState) -> str:
    """Decision point to determine the next step based on the current state."""
    print("---ROUTING---")
    if state.get("category"):
        print("Category found. Ending execution.")
        return END
    
    # Check which nodes have already run to decide where to go next
    # This logic assumes a sequential flow and checks if a node has been attempted
    # A more robust way could be to add a 'last_run_node' to the state.
    if state.get("reasoning") is None: # No node has run yet, should not happen with set entry point
         return "db_matcher"
    elif "DB" in state.get("reasoning", "") or state.get("reasoning") is None: # After DB
        if not state.get("category"):
            print("DB failed. Proceeding to Regex.")
            return "regex_matcher"
    elif "Regex" in state.get("reasoning", ""): # After Regex
        if not state.get("category"):
            print("Regex failed. Proceeding to LLM.")
            return "llm_categorizer"
            
    # As a fallback, if a category is found, we end.
    print("No specific route matched, ending.")
    return END

# --- Graph Definition ---
def build_graph():
    """Builds and compiles the conditional LangGraph state machine."""
    categorizer = StateGraph(AgentState)

    # Add nodes
    categorizer.add_node("db_matcher", db_matcher_node)
    categorizer.add_node("regex_matcher", regex_matcher_node)
    categorizer.add_node("llm_categorizer", llm_categorizer_node)

    # Define the graph's flow
    categorizer.set_entry_point("db_matcher")
    
    # After each step, check if we're done or need to continue
    categorizer.add_conditional_edges(
        "db_matcher",
        lambda s: END if s.get("category") else "regex_matcher",
        {"regex_matcher": "regex_matcher", END: END}
    )
    categorizer.add_conditional_edges(
        "regex_matcher",
        lambda s: END if s.get("category") else "llm_categorizer",
        {"llm_categorizer": "llm_categorizer", END: END}
    )
    # The LLM is the last step, so it always ends.
    categorizer.add_edge("llm_categorizer", END)
    
    return categorizer.compile()

# Compile once globally for reuse
graph = build_graph()

# --- Main Execution Block ---
def run_categorizer(input_text: str, user_id: Optional[str] = None) -> dict:
    """Normalizes input text and runs it through the categorization graph."""
    normalized_input_text = normalize_text(input_text)
    input_state: AgentState = {"input_text": normalized_input_text}
    result = graph.invoke(input_state)
    return result

if __name__ == "__main__":
    test_inputs = [
        "Uber ride to airport GHS 25.50",
        "POS TRXN - Groceries USD 50.00",
        "Momo payment for electricity bill",
        "KFC order via UberEats",
        "Monthly payment for my apartment", # Should be caught by Regex 'rent'
        "Subscription for cloud storage",
        "Donation to charity",
        "Random gibberish transaction",
        "Paid for my uber ride and groceries", # Should be DB or Regex
        "Monthly electricity bill", # Should be Regex
        "Rent paid for April", # Should be DB or Regex
        "Data bundle recharge", # Should be DB or Regex
        "Bought a new gadget from Amazon", # Should go to LLM
        "Dinner at a fancy restaurant", # Should go to LLM
        "Subscription for cloud storage", # Should go to LLM
        "Donation to charity", # Should go to LLM
        "Unknown expense", # Should be Unknown
        "POS TRXN - Groceries USD 50.00", # New test case for normalization
        "Uber ride to airport GHS 25.50", # New test case for normalization
        "Momo payment for electricity bill", # New test case for normalization
        "KFC order via UberEats" # New test case for normalization
    ]

    for input_text in test_inputs:
        print("\n" + "="*40)
        print(f"Invoking graph with raw input: '{input_text}'")
        final_state = run_categorizer(input_text)
        print("\n--- FINAL RESULT ---")
        print(f"  Category: {final_state.get('category')}")
        print(f"  Reasoning: {final_state.get('reasoning')}")
        print(f"  Confidence: {final_state.get('confidence_score')}")
        print("="*40)
