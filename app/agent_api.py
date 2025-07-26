from fastapi import APIRouter, HTTPException
from app.models import CategorizeRequest, CategorizeResponse, FeedbackRequest, Session, Interaction, CategorizedExpense, KeywordCategory, KeywordAddRequest
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

def update_keyword_db(keyword: str, category: str, user_id: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if the keyword already exists for this category and user
    cursor.execute("SELECT * FROM keyword_category WHERE keyword = ? AND category = ? AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))", (keyword, category, user_id, user_id))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO keyword_category (keyword, category, user_id) VALUES (?, ?, ?)", (keyword, category, user_id))
        conn.commit()
        print(f"Added '{keyword}' to category '{category}' for user '{user_id}' in DB.")
    else:
        print(f"Keyword '{keyword}' already exists for category '{category}' and user '{user_id}'. No update needed.")
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
def categorize_expense(req: CategorizeRequest, session_id: str = None, user_id: str = None):
    if not session_id:
        session_id = create_session(user_id=user_id or "default_user") # Use provided user_id or default
    
    log_interaction(session_id, "categorize_request", input_data=req.input_text)

    result = run_categorizer(req.input_text, user_id=user_id)

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
def submit_feedback(feedback: FeedbackRequest, session_id: str = None, user_id: str = None):
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

        # Update keyword DB based on feedback, now with user_id
        # Only update if confidence was low and correction was made
        if feedback.confidence_score is not None and feedback.confidence_score < 0.7 and \
           feedback.predicted_category != feedback.corrected_category:
            update_keyword_db(feedback.input_text, feedback.corrected_category, user_id)

        return {"message": "Feedback received and stored successfully!"}
    except Exception as e:
        print(f"Error storing feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to store feedback: {e}")

@router.post("/sessions", response_model=Session)
def start_new_session(user_id: str = None, metadata: str = None):
    print(f"DEBUG: Backend received request to start new session for user_id: {user_id}")
    session_id = create_session(user_id, metadata)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    session_data = cursor.fetchone()
    conn.close()
    if session_data:
        print(f"DEBUG: Session created successfully: {session_id}")
        return Session(**session_data)
    print("DEBUG: Failed to create session in backend.")
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

@router.post("/keywords", response_model=KeywordCategory)
def add_keyword(keyword_data: KeywordAddRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO keyword_category (user_id, keyword, category) VALUES (?, ?, ?)",
            (keyword_data.user_id, keyword_data.keyword, keyword_data.category)
        )
        conn.commit()
        keyword_id = cursor.lastrowid
        conn.close()
        return KeywordCategory(id=keyword_id, **keyword_data.dict())
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Keyword already exists for this user or globally.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add keyword: {e}")

@router.get("/keywords", response_model=list[KeywordCategory])
def get_keywords(user_id: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT id, user_id, keyword, category FROM keyword_category WHERE user_id = ? OR user_id IS NULL", (user_id,))
    else:
        cursor.execute("SELECT id, user_id, keyword, category FROM keyword_category WHERE user_id IS NULL")
    keywords_data = cursor.fetchall()
    conn.close()
    return [KeywordCategory(**keyword) for keyword in keywords_data]

@router.get("/categorize")
def categorize_example():
    return {"message": "Send a POST request with input_text to categorize."}
