from fastapi import APIRouter, HTTPException
from app.models import CategorizeRequest, CategorizeResponse, FeedbackRequest, Session, Interaction, CategorizedExpense
from app.agent import run_categorizer
import sqlite3
import uuid
from datetime import datetime

router = APIRouter()

# Database connection for feedback storage
def get_db_connection():
    conn = sqlite3.connect("data/keywords.db")
    conn.row_factory = sqlite3.Row
    return conn

def update_keyword_db(keyword: str, category: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if the keyword already exists for this category
    cursor.execute("SELECT * FROM keyword_category WHERE keyword = ? AND category = ?", (keyword, category))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO keyword_category (keyword, category) VALUES (?, ?)", (keyword, category))
        conn.commit()
        print(f"Added '{keyword}' to category '{category}' in DB.")
    else:
        print(f"Keyword '{keyword}' already exists for category '{category}'. No update needed.")
    conn.close()

def log_categorization(input_text: str, category: str, matching_method: str, confidence_score: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO categorization_log (input_text, final_category, matching_method, confidence_score) VALUES (?, ?, ?, ?)",
        (input_text, category, matching_method, confidence_score)
    )
    conn.commit()
    conn.close()
    print(f"Logged categorization: {input_text} -> {category} ({matching_method}, {confidence_score})")

def create_session(user_id: str = None, metadata: str = None):
    session_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (session_id, user_id, metadata) VALUES (?, ?, ?)",
        (session_id, user_id, metadata)
    )
    conn.commit()
    conn.close()
    return session_id

def update_session_last_active(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET last_active_time = CURRENT_TIMESTAMP WHERE session_id = ?",
        (session_id,)
    )
    conn.commit()
    conn.close()

def log_interaction(session_id: str, interaction_type: str, input_data: str = None, output_data: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO interactions (session_id, interaction_type, input_data, output_data) VALUES (?, ?, ?, ?)",
        (session_id, interaction_type, input_data, output_data)
    )
    conn.commit()
    conn.close()
    update_session_last_active(session_id)

def log_categorized_expense(session_id: str, description: str, amount: float, category: str, confidence_score: float, raw_input: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO categorized_expenses (session_id, description, amount, category, confidence_score, raw_input) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, description, amount, category, confidence_score, raw_input)
    )
    conn.commit()
    conn.close()
    update_session_last_active(session_id)

@router.post("/categorize", response_model=CategorizeResponse)
def categorize_expense(req: CategorizeRequest, session_id: str = None):
    if not session_id:
        session_id = create_session(user_id="default_user") # You might want to get user_id from auth
    
    log_interaction(session_id, "categorize_request", input_data=req.input_text)

    result = run_categorizer(req.input_text)

    # Log the categorization event
    log_categorization(
        req.input_text,
        result["category"] or "Unknown",
        result.get("matching_method", "Unknown"),
        result.get("confidence_score", 0.0)
    )

    log_categorized_expense(
        session_id,
        description=req.input_text, # Assuming description is the input text for now
        amount=0.0, # Placeholder, as amount is not in current request
        category=result["category"] or "Unknown",
        confidence_score=result.get("confidence_score", 0.0),
        raw_input=req.input_text
    )
    
    log_interaction(session_id, "categorize_response", output_data=str(result))

    return CategorizeResponse(
        category=result["category"] or "Unknown",
        reasoning=result["reasoning"] or "No reasoning provided",
        confidence_score=result.get("confidence_score"),
        matching_method=result.get("matching_method")
    )

@router.post("/feedback")
def submit_feedback(feedback: FeedbackRequest, session_id: str = None):
    if session_id:
        log_interaction(session_id, "feedback_submission", input_data=str(feedback))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (input_text, predicted_category, corrected_category, reasoning, confidence_score) VALUES (?, ?, ?, ?, ?)",
            (
                feedback.input_text,
                feedback.predicted_category,
                feedback.corrected_category,
                feedback.reasoning,
                feedback.confidence_score,
            ),
        )
        conn.commit()
        conn.close()

        # Update keyword DB based on feedback
        update_keyword_db(feedback.input_text, feedback.corrected_category)

        return {"message": "Feedback received and stored successfully!"}
    except Exception as e:
        print(f"Error storing feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store feedback: {e}")

@router.post("/sessions", response_model=Session)
def start_new_session(user_id: str = None, metadata: str = None):
    session_id = create_session(user_id, metadata)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    session_data = cursor.fetchone()
    conn.close()
    if session_data:
        return Session(**session_data)
    raise HTTPException(status_code=500, detail="Failed to create session.")

@router.get("/sessions/{session_id}", response_model=Session)
def get_session(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    session_data = cursor.fetchone()
    conn.close()
    if session_data:
        return Session(**session_data)
    raise HTTPException(status_code=404, detail="Session not found.")

@router.get("/interactions/{session_id}", response_model=list[Interaction])
def get_interactions(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interactions WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    interactions_data = cursor.fetchall()
    conn.close()
    return [Interaction(**interaction) for interaction in interactions_data]

@router.get("/categorized_expenses/{session_id}", response_model=list[CategorizedExpense])
def get_categorized_expenses(session_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categorized_expenses WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
    expenses_data = cursor.fetchall()
    conn.close()
    return [CategorizedExpense(**expense) for expense in expenses_data]

@router.get("/categorize")
def categorize_example():
    return {"message": "Send a POST request with input_text to categorize."}
