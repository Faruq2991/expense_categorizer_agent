# Expense Categorizer – Improvement Plan

## ✅ What's Working
- FastAPI backend with keyword DB + regex matcher + LLM fallback
- Feedback loop with DB persistence
- Streamlit frontend for input + categorization
- Multi-channel interaction (Telegram, SMS)

---

## Backend Improvements
### 1. Consistent Categorizer Output
Ensure every tool (`Regex`, `DB`, `LLM`) returns:
- `category`
- `reasoning`
- `matching_method`
- `confidence_score`
**Status: Implemented**

### 2. Input Validation
Add Pydantic request models with detailed error messages.
**Status: Implemented**

### 3. Feedback Intelligence
Auto-add correct categorization as keyword if confidence is low.
**Status: Implemented** (Conditional auto-add based on confidence and correction)

---

## Streamlit UI Improvements
### 1. Categorization History
- Show session-level log of inputs + categories.
- Include matching method and confidence.
**Status: Implemented**

### 2. Keyword Manager
- Add, edit, delete keywords.
- Show current keyword-category mapping.
**Status: Partially Implemented** (Add and view keywords are implemented; edit/delete are not)

### 3. Feedback Interface
- Let users confirm or reject a categorization.
- Save feedback and optionally update DB.
**Status: Implemented**

### 4. Bulk CSV Categorization
- Upload bank/export CSV.
- Batch categorize rows using FastAPI.
- Download enriched CSV.
**Status: Not Implemented**

---

## Natural Input Support
### 1. Preprocessing Pipeline
- Text Normalization: Remove common noise, handle abbreviations, lowercasing, remove extra whitespace.
- Integration: Applied before categorization.
**Status: Implemented**

---

## Multi-Channel Interaction
### 1. Telegram Bot Integration
- Receive expense descriptions via Telegram.
- Send categorized results back to Telegram.
**Status: Implemented**

### 2. SMS Integration (Twilio)
- Receive expense descriptions via SMS.
- Send categorized results back via SMS.
**Status: Implemented**

---

## Future Features
- User login (API key or local session)
- Visual dashboards for spending trends
- LangSmith tracing for agents
- Switch to PostgreSQL + SQLAlchemy for multi-user support
- Edit/Delete keywords in UI
- Bulk CSV Categorization
- Hybrid Matching (Regex + Embeddings)
- Multi-language Support
- Testing & Monitoring
- Mobile-First UX (Implemented)
- Real-Time Integrations
- Custom Category Profiles