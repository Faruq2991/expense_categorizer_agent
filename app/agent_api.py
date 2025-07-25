from fastapi import APIRouter
from app.models import CategorizeRequest, CategorizeResponse, FeedbackRequest
from app.agent import run_categorizer
import sqlite3

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

@router.post("/categorize", response_model=CategorizeResponse)
def categorize_expense(req: CategorizeRequest):
    result = run_categorizer(req.input_text)

    # Log the categorization event
    log_categorization(
        req.input_text,
        result["category"] or "Unknown",
        result.get("matching_method", "Unknown"),
        result.get("confidence_score", 0.0)
    )

    return CategorizeResponse(
        category=result["category"] or "Unknown",
        reasoning=result["reasoning"] or "No reasoning provided",
        confidence_score=result.get("confidence_score"),
        matching_method=result.get("matching_method")
    )

@router.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
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
        return {"message": f"Failed to store feedback: {e}"}, 500

@router.get("/categorize")
def categorize_example():
    return {"message": "Send a POST request with input_text to categorize."}
