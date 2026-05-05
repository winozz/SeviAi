"""
CvSU Chatbot REST API
FastAPI-based endpoint for integration with web applications
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import json
import os
import random
import re
import time
from collections import defaultdict
from datetime import datetime

import joblib
import nltk
from nltk.stem import WordNetLemmatizer

# Import logger
from api.logger import ChatLogger
# Import hybrid chatbot
from hybrid_chatbot import HybridChatbot

# Download NLTK resources
for resource in ['punkt_tab', 'wordnet']:
    try:
        nltk.data.find(f'tokenizers/{resource}')
    except LookupError:
        nltk.download(resource, quiet=True)

lemmatizer = WordNetLemmatizer()

# ============================================================================
# SYSTEM INSTRUCTIONS / AGENT PERSONALITY
# ============================================================================
SYSTEM_INSTRUCTIONS = """
You are Sevi, the CvSU Virtual Assistant - a helpful, friendly guide for Cavite State University.

CORE PERSONALITY:
- Professional yet approachable
- Patient and empathetic
- Always respectful of Filipino culture ("Iskolar para sa Bayan")
- Proactive in offering additional help

BEHAVIOR GUIDELINES:
1. Intent Recognition: Use the classified intent to provide relevant information
2. Fallback Handling: When confidence is low, politely ask for clarification
3. Tone: Warm, encouraging, supportive of student goals
4. Context Awareness: Remember user's intent to provide follow-up suggestions

RESPONSE PROTOCOLS:
- Always start with a relevant greeting if it's the first message
- Provide complete, actionable information
- Include contact details when relevant (email, phone, office)
- Offer next steps: "Is there anything else I can help you with?"
- For technical issues, suggest visiting the main campus or official website

PROHIBITED:
- Do NOT make up information not in the knowledge base
- Do NOT promise services beyond CvSU's scope
- Do NOT provide personal opinions on university policies

LANGUAGE:
- Primary: English (professional)
- Secondary: Filipino phrases accepted (e.g., "Salamat", "Iskolar para sa Bayan")
"""

# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(
    title="CvSU Chatbot API",
    description="REST API for Sevi, the CvSU Virtual Assistant",
    version="1.0.0"
)

# Enable CORS for web app integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the web interface as static files
app.mount("/web", StaticFiles(directory="web"), name="web")

# ============================================================================
# Request/Response Models
# ============================================================================
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    confidence: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    message_id: Optional[int] = None


class FeedbackRequest(BaseModel):
    message_id: Optional[int] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    intent: Optional[str] = None
    rating: Optional[int] = None          # 1–5 star quality score
    helpful: Optional[bool] = None        # thumbs up / thumbs down
    comment: Optional[str] = None         # freeform note or correction
    suggested_intent: Optional[str] = None  # user-supplied intent correction

class IntentInfo(BaseModel):
    tag: str
    pattern_count: int
    response_count: int
    sample_patterns: List[str]

class ModelInfo(BaseModel):
    model_name: str
    accuracy: float
    total_intents: int
    total_patterns: int
    model_size_kb: float
    system_instructions: str

# Note: HybridChatbot is now imported from hybrid_chatbot.py
# It combines Naive Bayes (fast) + Neural Network (accurate)

# ============================================================================
# COLLEGE COURSES DATA — for multi-turn selection conversation
# ============================================================================

COLLEGE_COURSES = {
    1: {
        "name": "College of Agriculture, Food, Environment and Natural Resources (CAFENR)",
        "programs": [
            "BS Agriculture (majors: Animal Science, Crop Science, Agricultural Economics, Soil Science)",
            "BS Agricultural Engineering",
            "BS Environmental Science",
            "BS Forestry",
            "BS Food Technology",
            "BS Agribusiness",
        ],
        "contact": "cafenr@cvsu.edu.ph",
    },
    2: {
        "name": "College of Arts and Sciences (CAS)",
        "programs": [
            "BA Communication / Journalism",
            "BA Psychology",
            "BS Biology",
            "BS Mathematics",
            "BS Statistics",
            "BS Physical Science",
            "BS Social Work",
            "BA Political Science",
            "BA Sociology",
        ],
        "contact": "cas@cvsu.edu.ph",
    },
    3: {
        "name": "College of Criminal Justice (CCJ)",
        "programs": [
            "BS Criminology",
        ],
        "contact": "ccj@cvsu.edu.ph",
    },
    4: {
        "name": "College of Economics, Management and Development Studies (CEMDS)",
        "programs": [
            "BS Business Administration (majors: Marketing, Financial Management, Human Resource Development)",
            "BS Entrepreneurship",
            "BS Public Administration",
            "BS Office Administration",
            "BS Economics",
            "BS Accountancy",
            "BS Management Accounting",
        ],
        "contact": "cemds@cvsu.edu.ph",
    },
    5: {
        "name": "College of Education (CED)",
        "programs": [
            "Bachelor of Elementary Education (BEEd)",
            "Bachelor of Secondary Education (BSEd) — majors: Math, English, Filipino, Science, Social Studies, TLE, MAPEH",
            "Bachelor of Early Childhood Education (BECEd)",
            "Bachelor of Special Needs Education (BSNEd)",
            "Bachelor of Physical Education (BPEd)",
            "Bachelor of Technical-Vocational Teacher Education (BTVTEd)",
        ],
        "contact": "ced@cvsu.edu.ph",
    },
    6: {
        "name": "College of Engineering and Information Technology (CEIT)",
        "programs": [
            "BS Computer Science (BSCS)",
            "BS Information Technology (BSIT)",
            "BS Computer Engineering (BSCpE)",
            "BS Electronics Engineering (BSECE)",
            "BS Civil Engineering (BSCE)",
            "BS Mechanical Engineering (BSME)",
            "BS Electrical Engineering (BSEE)",
            "BS Chemical Engineering (BSChE)",
        ],
        "contact": "ceit@cvsu.edu.ph",
    },
    7: {
        "name": "College of Medicine (COM) — established 2022",
        "programs": [
            "Doctor of Medicine (MD)",
        ],
        "contact": "com@cvsu.edu.ph",
        "note": "Requires a pre-med undergraduate degree. NMAT score is required for admission.",
    },
    8: {
        "name": "College of Nursing (CON)",
        "programs": [
            "BS Nursing (BSN)",
        ],
        "contact": "con@cvsu.edu.ph",
    },
    9: {
        "name": "College of Sports, Physical Education and Recreation (CSPER)",
        "programs": [
            "BS Exercise and Sports Science",
            "BS Physical Education",
            "BS Recreation Management",
        ],
        "contact": "csper@cvsu.edu.ph",
    },
    10: {
        "name": "College of Veterinary Medicine and Biomedical Sciences (CVMBS)",
        "programs": [
            "Doctor of Veterinary Medicine (DVM)",
            "BS Veterinary Technology",
            "BS Biomedical Sciences",
        ],
        "contact": "cvmbs@cvsu.edu.ph",
    },
    11: {
        "name": "College of Tourism and Hospitality Management (CTHM) — newest, 2025",
        "programs": [
            "BS Tourism Management",
            "BS Hospitality Management",
            "BS Travel Management",
        ],
        "contact": "cthm@cvsu.edu.ph",
    },
}

def _build_college_response(num: int) -> str:
    c = COLLEGE_COURSES[num]
    lines = [f"📚 {c['name']}", "", "PROGRAMS OFFERED:"]
    lines += [f"  • {p}" for p in c["programs"]]
    if "note" in c:
        lines += ["", f"NOTE: {c['note']}"]
    lines += ["", f"Contact: {c['contact']}"]
    lines += ["", "Type another number (1–11) to explore a different college, or ask me anything else!"]
    return "\n".join(lines)

# Per-user conversation context — tracks pending multi-turn states
# Structure: { user_id: { "pending": "college_selection" } }
conversation_contexts: dict = {}

# ============================================================================
# Initialize Chatbot and Logger
# ============================================================================
MODEL_DIR = "models"

# Initialize Hybrid Chatbot (Naive Bayes + Neural Network)
chatbot = HybridChatbot(
    model_dir=MODEL_DIR,
    responses_path=os.path.join(MODEL_DIR, "responses_map.json"),
    intents_db_path="data/cavsu_intents.db",
    intents_json_path="data/cavsu_intents.json"
)

# Initialize chat logger
chat_logger = ChatLogger(log_dir="logs", db_path="logs/chat_history.db")

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API status."""
    return {
        "service": "CvSU Chatbot API",
        "assistant_name": "Sevi",
        "status": "active",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": chatbot.nb_model is not None,
        "intents_available": chatbot.total_intents
    }

@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Send a message to the chatbot (Hierarchical Hybrid Model).

    Uses Naive Bayes first (fast), falls back to Neural Network if uncertain.
    Supports multi-turn college selection: after listing colleges, a number
    reply (1-11) returns that college's programs without going through the
    intent classifier.

    Request:
        message (str): User's question or input
        user_id (str, optional): Track conversation per user
        session_id (str, optional): Track conversation per session

    Returns:
        response (str): Chatbot's response
        intent (str): Classified intent
        confidence (float): Confidence score (0-1)
    """
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user_id = request.user_id or "anonymous"
    start_time = time.time()

    # ------------------------------------------------------------------
    # Multi-turn context: intercept numbered selection after college list
    # ------------------------------------------------------------------
    ctx = conversation_contexts.get(user_id, {})
    if ctx.get("pending") == "college_selection":
        num_match = re.fullmatch(r"\s*(\d+)\s*", request.message.strip())
        if num_match:
            num = int(num_match.group(1))
            if 1 <= num <= 11:
                # Keep the pending state so the user can keep browsing colleges
                college_response = _build_college_response(num)
                response_time_ms = (time.time() - start_time) * 1000
                message_id = chat_logger.log_chat(
                    user_id=user_id,
                    user_message=request.message,
                    bot_response=college_response,
                    intent="courses_offered",
                    confidence=1.0,
                    model_used="context",
                    session_id=request.session_id,
                    response_time_ms=response_time_ms,
                )
                return ChatResponse(
                    response=college_response,
                    intent="courses_offered",
                    confidence=1.0,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    message_id=message_id,
                )
            else:
                # Number out of range — gently re-prompt, keep state
                return ChatResponse(
                    response=f"Please enter a number between 1 and 11 to select a college, or ask me something else!",
                    intent="courses_offered",
                    confidence=1.0,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    message_id=None,
                )
        else:
            # Non-numeric reply — clear the pending state and fall through normally
            conversation_contexts.pop(user_id, None)

    # ------------------------------------------------------------------
    # Normal chatbot processing
    # ------------------------------------------------------------------
    intent, response, confidence, model_used = chatbot.chat(
        request.message,
        user_id=request.user_id,
        session_id=request.session_id
    )

    response_time_ms = (time.time() - start_time) * 1000

    # If the bot just listed the colleges, set the selection context
    if intent == "courses_offered":
        conversation_contexts[user_id] = {"pending": "college_selection"}

    # Log the chat
    message_id = chat_logger.log_chat(
        user_id=user_id,
        user_message=request.message,
        bot_response=response,
        intent=intent,
        confidence=confidence,
        model_used=model_used,
        session_id=request.session_id,
        response_time_ms=response_time_ms
    )

    return ChatResponse(
        response=response,
        intent=intent,
        confidence=confidence,
        user_id=request.user_id,
        session_id=request.session_id,
        message_id=message_id
    )

@app.get("/intents", tags=["Intents"])
async def get_intents():
    """Get list of all available intent categories."""
    intents = chatbot.get_all_intents()
    return {
        "total_intents": len(intents),
        "intents": intents
    }

@app.get("/intents/{intent_tag}", tags=["Intents"])
async def get_intent(intent_tag: str):
    """Get details about a specific intent."""
    details = chatbot.get_intent_details(intent_tag)

    if not details:
        raise HTTPException(status_code=404, detail=f"Intent '{intent_tag}' not found")

    return details

@app.get("/model/info", response_model=ModelInfo, tags=["Model"])
async def model_info():
    """Get information about the trained model."""
    return ModelInfo(
        model_name=chatbot.model_name,
        accuracy=chatbot.accuracy,
        total_intents=chatbot.total_intents,
        total_patterns=chatbot.total_patterns,
        model_size_kb=chatbot.model_size_kb,
        system_instructions=chatbot.system_instructions
    )

@app.get("/model/instructions", tags=["Model"])
async def get_instructions():
    """Get agent system instructions."""
    return {
        "instructions": chatbot.system_instructions,
        "version": "1.0.0"
    }

@app.get("/conversation/{user_id}", tags=["Conversation"])
async def get_conversation_history(user_id: str):
    """Get conversation history for a user."""
    history = chatbot.conversation_history.get(user_id, [])
    return {
        "user_id": user_id,
        "message_count": len(history),
        "conversation": history
    }

@app.delete("/conversation/{user_id}", tags=["Conversation"])
async def clear_conversation(user_id: str):
    """Clear conversation history for a user."""
    if user_id in chatbot.conversation_history:
        del chatbot.conversation_history[user_id]
        return {"status": "cleared", "user_id": user_id}
    return {"status": "no_history", "user_id": user_id}

@app.post("/batch", tags=["Chat"])
async def batch_chat(requests: List[ChatRequest]):
    """
    Process multiple chat requests in batch.

    Useful for integration with web apps that need multiple responses.
    """
    results = []
    for request in requests:
        start_time = time.time()
        intent, response, confidence, model_used = chatbot.chat(request.message)
        response_time_ms = (time.time() - start_time) * 1000

        # Log each message
        chat_logger.log_chat(
            user_id=request.user_id or "anonymous",
            user_message=request.message,
            bot_response=response,
            intent=intent,
            confidence=confidence,
            model_used=model_used,
            session_id=request.session_id,
            response_time_ms=response_time_ms
        )

        results.append(ChatResponse(
            response=response,
            intent=intent,
            confidence=confidence,
            user_id=request.user_id
        ))
    return {"count": len(results), "results": results}

# ============================================================================
# Logging Endpoints
# ============================================================================

@app.get("/logs/user/{user_id}", tags=["Logging"])
async def get_user_logs(user_id: str, limit: int = 50):
    """Get chat history for a specific user"""
    history = chat_logger.get_user_history(user_id, limit)
    return {
        "user_id": user_id,
        "message_count": len(history),
        "messages": history
    }

@app.get("/logs/session/{session_id}", tags=["Logging"])
async def get_session_logs(session_id: str):
    """Get all messages in a specific session"""
    history = chat_logger.get_session_history(session_id)
    return {
        "session_id": session_id,
        "message_count": len(history),
        "messages": history
    }

@app.get("/logs/intents", tags=["Logging"])
async def get_intent_logs():
    """Get statistics for all intents"""
    stats = chat_logger.get_intent_statistics()
    return {
        "total_intents": len(stats),
        "intents": stats
    }

@app.get("/logs/sessions", tags=["Logging"])
async def get_sessions_list(user_id: Optional[str] = None, limit: int = 20):
    """Get list of sessions"""
    sessions = chat_logger.get_session_list(user_id, limit)
    return {
        "user_id": user_id,
        "session_count": len(sessions),
        "sessions": sessions
    }

@app.get("/logs/today", tags=["Logging"])
async def get_today_statistics():
    """Get today's chat statistics"""
    stats = chat_logger.get_today_stats()
    return stats

@app.get("/logs/search", tags=["Logging"])
async def search_logs(query: str, limit: int = 20):
    """Search logs by message content"""
    results = chat_logger.search_logs(query, limit)
    return {
        "query": query,
        "results_count": len(results),
        "results": results
    }

@app.get("/logs/fallbacks", tags=["Logging"])
async def get_fallback_logs(limit: int = 100):
    """Get recent fallback user utterances for learning and analysis."""
    fallback_examples = chat_logger.get_fallback_examples(limit)
    return {
        "fallback_count": len(fallback_examples),
        "fallbacks": fallback_examples
    }

# ============================================================================
# Feedback Endpoints
# ============================================================================

@app.post("/feedback", tags=["Feedback"])
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback for a specific bot response.

    Body fields:
        message_id (int, optional): ID of the chat_messages row being rated
        rating (int, optional): Quality score 1–5
        helpful (bool, optional): True = thumbs up, False = thumbs down
        comment (str, optional): Freeform note or correction
        suggested_intent (str, optional): User-supplied intent correction
        user_id / session_id (str, optional): For cross-referencing
        intent (str, optional): Intent tag of the rated response
    """
    if request.rating is not None and not (1 <= request.rating <= 5):
        raise HTTPException(status_code=400, detail="rating must be between 1 and 5")
    if request.rating is None and request.helpful is None and not request.comment:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of: rating, helpful, or comment"
        )

    feedback_id = chat_logger.log_feedback(
        message_id=request.message_id,
        user_id=request.user_id,
        session_id=request.session_id,
        intent=request.intent,
        rating=request.rating,
        helpful=request.helpful,
        comment=request.comment,
        suggested_intent=request.suggested_intent
    )

    if feedback_id is None:
        raise HTTPException(status_code=500, detail="Failed to save feedback")

    return {"status": "ok", "feedback_id": feedback_id}


@app.get("/feedback/stats", tags=["Feedback"])
async def get_feedback_stats():
    """
    Aggregate feedback statistics.

    Returns:
        total_feedback: Total number of feedback entries
        avg_rating: Overall average star rating
        helpful_pct: Percentage of 'helpful' responses
        by_intent: Per-intent breakdown (count, avg_rating, helpful_pct, unhelpful_count)
        low_rated_intents: Worst-performing intents (min 3 ratings)
        recent_comments: Last 10 freeform comments with metadata
    """
    return chat_logger.get_feedback_stats()


@app.get("/feedback", tags=["Feedback"])
async def get_feedback(
    limit: int = 100,
    helpful: Optional[bool] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    intent: Optional[str] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None
):
    """Retrieve feedback records, optionally joined with the source message."""
    limit = max(1, min(limit, 5000))
    entries = chat_logger.get_feedback_entries(
        limit=limit,
        helpful=helpful,
        user_id=user_id,
        session_id=session_id,
        intent=intent,
        min_rating=min_rating,
        max_rating=max_rating
    )
    return {
        "count": len(entries),
        "feedback": entries
    }

@app.post("/logs/export/{user_id}", tags=["Logging"])
async def export_user_logs(user_id: str):
    """Export all data for a user as JSON file"""
    filepath = chat_logger.export_user_data(user_id)
    if filepath:
        return {
            "status": "success",
            "user_id": user_id,
            "filepath": filepath,
            "message": f"User data exported to {filepath}"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to export user data")

@app.delete("/logs/cleanup", tags=["Logging"])
async def cleanup_old_logs(days: int = 30):
    """Delete logs older than specified days"""
    deleted = chat_logger.cleanup_old_logs(days)
    return {
        "status": "success",
        "days": days,
        "deleted_entries": deleted,
        "message": f"Deleted {deleted} log entries older than {days} days"
    }

# ============================================================================
# Error Handlers
# ============================================================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return {
        "error": True,
        "status_code": exc.status_code,
        "message": exc.detail
    }

# ============================================================================
# Run Server
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
