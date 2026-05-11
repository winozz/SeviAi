"""
CvSU Chatbot REST API
FastAPI-based endpoint for integration with web applications
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
import asyncio
import json
import os
import random
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import joblib
import nltk
from nltk.stem import WordNetLemmatizer

# Import logger
from .logger import ChatLogger
# Import hybrid chatbot
from .hybrid_chatbot import HybridChatbot

# Download NLTK resources (idempotent — no-op if already present)
for resource, kind in [('punkt_tab', 'tokenizers'), ('wordnet', 'corpora')]:
    try:
        nltk.data.find(f'{kind}/{resource}')
    except (LookupError, OSError):
        nltk.download(resource, quiet=True)

lemmatizer = WordNetLemmatizer()

# ============================================================================
# SYSTEM INSTRUCTIONS / AGENT PERSONALITY
# ============================================================================
SYSTEM_INSTRUCTIONS = """
You are Sevi, the CvSU Virtual Assistant - a helpful, friendly guide for Cavite State University.

1. IDENTITY AND SCOPE
- You serve prospective students, current students, parents, faculty, and the general public.
- You cover academic programs, admissions, campus services, scholarships, fees, schedules, policies, and general information about CvSU's main campus in Indang and its satellite campuses (Imus, Rosario, Silang, Naic, Trece Martires, Tanza, General Trias, Carmona, Cavite City, Bacoor, and others).
- You do NOT process enrollment, payments, or official document requests. Always redirect high-stakes actions (enrollment, grade disputes, document authentication) to the proper office.

2. CORE PERSONALITY
- Professional yet approachable; warm and respectful of Filipino culture ("Iskolar para sa Bayan").
- Patient and empathetic - many users are first-generation applicants or parents unfamiliar with university processes. Avoid jargon without explanation.
- Proactive in offering next steps and pointing to verification.

3. RETRIEVAL AND VERIFICATION PROTOCOL
Before answering a factual question:
- Classify the query: (a) general/stable, (b) time-sensitive, (c) campus-specific, (d) personal/transactional.
- Time-sensitive items (deadlines, fees, schedules, CvSUAT dates) must be flagged for verification with the relevant office. Qualify with "as of [date], please verify with [office]."
- For any specific number, date, name, or requirement, cite the source or qualify clearly.
- Disambiguate campus before giving program-specific or fee-specific answers - CvSU Indang and CvSU Imus may have very different offerings.

4. CONFIDENCE TIERS - never blur these
- High confidence: from official, recently verified CvSU sources. State plainly.
- Medium confidence: from official sources but possibly outdated. State with date qualifier and recommend verification.
- Low confidence: from secondary sources, inference, or older data. State as such and direct the user to the relevant office.
- No information: admit the gap honestly. Never fabricate. Provide the contact path of who would know.

5. DISAMBIGUATION
When a query is ambiguous, ask one targeted clarifying question, e.g.:
- "CvSU has multiple campuses. Which one are you asking about?"
- "Are you asking as a freshman applicant, transferee, or graduate student?"
- "Which academic year - 2025-2026 or 2026-2027?"
Limit to one clarifying question per turn unless absolutely necessary.

6. RESPONSE STRUCTURE
- Direct answer first, supporting details second, caveats and verification reminders last.
- Include contact info for the specific office when relevant.
- Short answers for simple lookups; longer structured answers for process questions.
- Offer next steps: "Is there anything else I can help you with?"

7. LANGUAGE
- Primary: English (professional). Respond in the language the user uses; if they mix Tagalog and English (Taglish), respond in kind.
- Use formal Filipino academic terminology when discussing official terms (e.g., "Pagsusulit sa Pagpasok," "Rehistrar").

8. PRIVACY AND DATA HANDLING (RA 10173)
- Never request or store personal information (full name, student number, contact details) unless the platform explicitly supports secure data handling.
- Never speculate about specific students' grades, status, or records.
- Redirect all individual student inquiries to the registrar or guidance office.

9. ESCALATION PATHWAYS - surface the right office
- Admissions questions -> Office of Admissions, specific campus
- Enrollment issues -> Registrar, specific campus
- Financial concerns -> Cashier and Scholarship Office (note RA 10931 free higher education subsidy where applicable)
- Academic concerns -> department chair or college dean
- Student welfare -> Office of Student Affairs and Services (OSAS)
- Online system issues -> Management Information Systems (MIS) office
- Complaints/appeals -> Campus Administrator or University President's Office

10. REFUSAL AND REDIRECTION
Decline to:
- Predict admission outcomes for specific applicants.
- Compare CvSU unfavorably to other institutions in misleading ways.
- Give legal interpretations of university policies (refer to the official policy documents).
- Provide unofficial workarounds to academic requirements.
- Share contact details of individual faculty without official verification.

11. PROHIBITED
- Do NOT fabricate tuition figures, professor names, deadlines, course codes, or passing rates.
- Do NOT promise services beyond CvSU's scope.
- Do NOT provide personal opinions on university policies.
- Do NOT give a generic "CvSU" answer without first asking which campus when the campus matters.

12. META
You are a helpful starting point and information aggregator, not the final authority. For anything consequential - enrollment, scholarships, document requirements - empower the user to verify with the proper CvSU office, and provide the path to that verification.
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

# ============================================================================
# Request/Response Models
# ============================================================================
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

# Campus map (48 official locations) — see api/campus_places.py
from api.campus_places import (
    MapData,
    PlaceMeta,
    resolve_map_data as _resolve_map_data,
    build_place_meta as _build_place_meta,
    campus_map_payload as _campus_map_payload,
    has_place as _has_place,
)

class ChatResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    response: str
    intent: str
    confidence: float
    model_used: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    entities: Optional[dict] = None
    is_follow_up: Optional[bool] = None
    message_id: Optional[int] = None
    map_data: Optional[MapData] = None

class IntentInfo(BaseModel):
    tag: str
    pattern_count: int
    response_count: int
    sample_patterns: List[str]

class ModelInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_name: str
    accuracy: float
    total_intents: int
    total_patterns: int
    model_size_kb: float
    system_instructions: str

class FeedbackRequest(BaseModel):
    message_id: Optional[int] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    intent: Optional[str] = None
    rating: Optional[int] = None          # 1–5
    helpful: Optional[bool] = None
    comment: Optional[str] = None
    suggested_intent: Optional[str] = None
    user_message: Optional[str] = None    # store query directly when message_id unavailable

class FeedbackAnalyzeRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    intent: Optional[str] = None
    min_rating: Optional[int] = None
    max_rating: Optional[int] = None
    helpful: Optional[bool] = None
    limit: int = 5000
    apply: bool = False                   # write changes to cavsu_intents.json

# Note: HybridChatbot is now imported from hybrid_chatbot.py
# It combines Naive Bayes (fast) + Neural Network (accurate)

# ============================================================================
# Initialize Chatbot and Logger
# ============================================================================
MODEL_DIR = "models"

# Initialize Hybrid Chatbot (Naive Bayes + Neural Network)
chatbot = HybridChatbot(
    model_dir=MODEL_DIR,
    responses_path=os.path.join(MODEL_DIR, "responses_map.json")
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
        "intents_available": len(chatbot.responses_map)
    }

@app.post("/chat", response_model=ChatResponse, tags=["Chat"],
          responses={400: {"description": "Message cannot be empty"}})
async def chat_endpoint(request: ChatRequest):
    """
    Send a message to the chatbot (Hierarchical Hybrid Model).

    Uses Naive Bayes first (fast), falls back to Neural Network if uncertain.

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

    # Measure response time
    start_time = time.time()

    # Get response from hybrid chatbot with NLU enhancements
    intent, response, confidence, model_used, nlu_data = chatbot.chat(
        request.message,
        user_id=request.user_id,
        session_id=request.session_id
    )

    response_time_ms = (time.time() - start_time) * 1000

    # Log the chat
    message_id = chat_logger.log_chat(
        user_id=request.user_id or "anonymous",
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
        model_used=model_used,
        user_id=request.user_id,
        session_id=request.session_id,
        entities=nlu_data.get("entities", {}),
        is_follow_up=nlu_data.get("is_follow_up", False),
        message_id=message_id,
        map_data=_resolve_map_data(request.message, intent),
    )

@app.get("/intents", tags=["Intents"])
async def get_intents():
    """Get list of all available intent categories."""
    intents = chatbot.get_all_intents()
    return {
        "total_intents": len(intents),
        "intents": intents
    }

# ============================================================================
# Campus Map Endpoints
# ============================================================================

@app.get("/map", tags=["Map"])
async def get_campus_map():
    """Return the full set of campus places, the gate position, and the SVG viewBox.

    Edit `api/campus_places.py` server-side to change labels, geometry, walk
    times, or directions without recompiling the frontend.
    """
    return _campus_map_payload()

@app.get("/map/{place_id}", response_model=PlaceMeta, tags=["Map"],
         responses={404: {"description": "Place not found"}})
async def get_place(place_id: str):
    """Return canonical metadata for a single campus place."""
    if not _has_place(place_id):
        raise HTTPException(status_code=404, detail=f"Place '{place_id}' not found")
    return _build_place_meta(place_id)

@app.get("/intents/{intent_tag}", tags=["Intents"],
         responses={404: {"description": "Intent not found"}})
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
        intent, response, confidence, model_used, nlu_data = chatbot.chat(
            request.message,
            user_id=request.user_id,
            session_id=request.session_id
        )
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
            model_used=model_used,
            user_id=request.user_id,
            session_id=request.session_id,
            entities=nlu_data.get("entities", {}),
            is_follow_up=nlu_data.get("is_follow_up", False),
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

@app.post("/logs/export/{user_id}", tags=["Logging"],
          responses={500: {"description": "Export failed"}})
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
# Feedback Endpoints
# ============================================================================

def _extract_new_patterns(
    entries: List[Dict],
    intent_map: Dict[str, Any],
    existing_patterns: Dict[str, set],
) -> Dict[str, List[str]]:
    """Return new patterns derived from feedback entries, grouped by intent tag."""
    additions: Dict[str, List[str]] = defaultdict(list)
    for entry in entries:
        target = entry.get("suggested_intent")
        query = (entry.get("user_message") or "").strip()
        helpful = entry.get("helpful")
        rating = entry.get("rating")

        if not target and helpful is True and rating is not None and rating <= 3:
            target = entry.get("intent")

        if not target or not query or target not in intent_map:
            continue
        if query in existing_patterns[target]:
            continue

        intent_map[target]["patterns"].append(query)
        existing_patterns[target].add(query)
        additions[target].append(query)
    return additions


@app.post(
    "/feedback",
    tags=["Feedback"],
    responses={
        422: {"description": "rating must be an integer between 1 and 5"},
        500: {"description": "Failed to store feedback"},
    },
)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback for a bot response.

    Stores a rating, helpful flag, optional comment, and an optional
    suggested_intent correction for misclassified messages.
    Pass user_message when message_id is unavailable so the analyze
    endpoint can still extract training patterns.
    """
    if request.rating is not None and not (1 <= request.rating <= 5):
        raise HTTPException(status_code=422, detail="rating must be between 1 and 5")

    feedback_id = chat_logger.log_feedback(
        message_id=request.message_id,
        user_id=request.user_id,
        session_id=request.session_id,
        intent=request.intent,
        rating=request.rating,
        helpful=request.helpful,
        comment=request.comment,
        suggested_intent=request.suggested_intent,
        user_message=request.user_message,
    )

    if feedback_id is None:
        raise HTTPException(status_code=500, detail="Failed to store feedback")

    return {"status": "ok", "feedback_id": feedback_id}


@app.get("/feedback", tags=["Feedback"])
async def get_feedback(
    limit: int = 100,
    helpful: Optional[bool] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    intent: Optional[str] = None,
    min_rating: Optional[int] = None,
    max_rating: Optional[int] = None,
):
    """
    Retrieve feedback entries, joined with the original chat message.

    All filter parameters are optional and can be combined.
    """
    entries = chat_logger.get_feedback_entries(
        limit=limit,
        helpful=helpful,
        user_id=user_id,
        session_id=session_id,
        intent=intent,
        min_rating=min_rating,
        max_rating=max_rating,
    )
    return {"count": len(entries), "feedback": entries}


@app.get("/feedback/stats", tags=["Feedback"])
async def get_feedback_stats():
    """
    Aggregated feedback statistics: overall totals, per-intent breakdown,
    lowest-rated intents, and the 10 most recent comments.
    """
    stats = chat_logger.get_feedback_stats()
    return stats


@app.get("/feedback/fallbacks", tags=["Feedback"])
async def get_feedback_fallbacks(limit: int = 100):
    """
    Return recent messages that triggered the nlu_fallback intent.
    Useful for manually identifying missing training patterns.
    """
    examples = chat_logger.get_fallback_examples(limit=limit)
    return {"count": len(examples), "fallbacks": examples}


@app.post("/feedback/analyze", tags=["Feedback"],
          responses={500: {"description": "Intent file not found or DB rebuild failed"}})
async def analyze_feedback(request: FeedbackAnalyzeRequest):
    """
    Batch feedback analysis — identify misclassified utterances from stored
    feedback and optionally patch them back into the intent dataset.

    Workflow:
    1. Pull feedback entries matching the supplied filters.
    2. For each unhelpful or low-rated entry that carries a suggested_intent,
       add the original user_message as a new training pattern for that intent
       (deduplication is automatic).
    3. If apply=true, overwrite data/cavsu_intents.json (a timestamped backup
       is created first) and rebuild the SQLite intent database.
       If apply=false (default), write a preview file instead so you can
       review changes before committing.

    Returns a summary of how many patterns were added per intent.
    """
    entries = chat_logger.get_feedback_entries(
        limit=request.limit,
        helpful=request.helpful,
        user_id=request.user_id,
        session_id=request.session_id,
        intent=request.intent,
        min_rating=request.min_rating,
        max_rating=request.max_rating,
    )

    if not entries:
        return {
            "status": "no_data",
            "message": "No feedback entries matched the supplied filters.",
            "filters": request.model_dump(),
            "patterns_added": 0,
            "by_intent": {}
        }

    # Resolve paths relative to the project root (two levels up from api/)
    root = Path(__file__).resolve().parents[1]
    intents_path = root / "data" / "cavsu_intents.json"
    db_path = root / "data" / "cavsu_intents.db"

    if not intents_path.exists():
        raise HTTPException(status_code=500, detail=f"Intent file not found: {intents_path}")

    raw = await asyncio.to_thread(intents_path.read_text, encoding="utf-8")
    intents_doc = json.loads(raw)

    intent_map: Dict[str, Any] = {i["tag"]: i for i in intents_doc["intents"]}
    existing_patterns: Dict[str, set] = {
        tag: set(i.get("patterns", [])) for tag, i in intent_map.items()
    }
    additions = _extract_new_patterns(entries, intent_map, existing_patterns)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    result: Dict[str, Any] = {
        "run_id": run_id,
        "entries_analyzed": len(entries),
        "patterns_added": sum(len(v) for v in additions.values()),
        "by_intent": dict(sorted(additions.items())),
        "apply": request.apply,
    }

    if not additions:
        result["status"] = "no_changes"
        result["message"] = "No new patterns identified from the filtered feedback."
        return result

    if request.apply:
        backup_path = root / "data" / f"cavsu_intents.backup_{run_id}.json"
        original_raw = await asyncio.to_thread(intents_path.read_text, encoding="utf-8")
        await asyncio.to_thread(backup_path.write_text, original_raw, encoding="utf-8")
        updated = json.dumps(intents_doc, indent=2, ensure_ascii=False)
        await asyncio.to_thread(intents_path.write_text, updated, encoding="utf-8")

        # Rebuild the SQLite intent database
        try:
            import sys
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            from intents_db import create_intents_database
            await asyncio.to_thread(
                create_intents_database,
                json_path=str(intents_path),
                db_path=str(db_path),
                recreate=True,
            )
            result["db_rebuilt"] = True
        except Exception as exc:
            result["db_rebuilt"] = False
            result["db_error"] = str(exc)

        result["status"] = "applied"
        result["backup_file"] = str(backup_path)
        result["output_file"] = str(intents_path)
        result["restart_api_required"] = True
    else:
        preview_path = root / "data" / f"cavsu_intents_preview_{run_id}.json"
        preview_text = json.dumps(intents_doc, indent=2, ensure_ascii=False)
        await asyncio.to_thread(preview_path.write_text, preview_text, encoding="utf-8")
        result["status"] = "preview"
        result["preview_file"] = str(preview_path)
        result["message"] = "Dry-run complete. Set apply=true to commit changes."

    return result


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
        host="127.0.0.1",
        port=8000,
        reload=False
    )

