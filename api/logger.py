"""
Chat Logging System for CvSU Chatbot
Logs all conversations, intents, and metadata to files and database
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import threading

class ChatLogger:
    """Handles all chat logging operations"""

    def __init__(self, log_dir: str = "logs", db_path: str = "logs/chat_history.db"):
        self.log_dir = Path(log_dir)
        self.db_path = db_path
        self.lock = threading.Lock()

        # Create directories
        self.log_dir.mkdir(exist_ok=True)

        # Initialize database
        self._init_database()

        print(f"[OK] Chat Logger initialized")
        print(f"  Logs directory: {self.log_dir}")
        print(f"  Database: {self.db_path}")

    def _init_database(self):
        """Initialize SQLite database for chat history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Chat messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    response_time_ms REAL,
                    model_used TEXT
                )
            """)

            # Ensure legacy DBs have the new column
            cursor.execute("PRAGMA table_info(chat_messages)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            if "model_used" not in existing_columns:
                cursor.execute("ALTER TABLE chat_messages ADD COLUMN model_used TEXT")

            # User sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    message_count INTEGER DEFAULT 0,
                    average_confidence REAL
                )
            """)

            # Intent statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS intent_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intent TEXT UNIQUE NOT NULL,
                    count INTEGER DEFAULT 0,
                    avg_confidence REAL,
                    last_used TEXT
                )
            """)

            # User feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    message_id INTEGER,
                    user_id TEXT,
                    session_id TEXT,
                    intent TEXT,
                    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                    helpful INTEGER CHECK(helpful IN (0, 1)),
                    comment TEXT,
                    suggested_intent TEXT,
                    user_message TEXT,
                    FOREIGN KEY (message_id) REFERENCES chat_messages(id)
                )
            """)

            # Migrate existing DBs that predate the user_message column
            cursor.execute("PRAGMA table_info(feedback)")
            fb_cols = [r[1] for r in cursor.fetchall()]
            if "user_message" not in fb_cols:
                cursor.execute("ALTER TABLE feedback ADD COLUMN user_message TEXT")

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR] Database initialization error: {e}")

    def log_chat(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        intent: str,
        confidence: float,
        model_used: Optional[str] = None,
        session_id: Optional[str] = None,
        response_time_ms: Optional[float] = None
    ) -> Optional[int]:
        """
        Log a single chat message to database and file

        Args:
            user_id: User identifier
            user_message: User's input
            bot_response: Bot's response
            intent: Classified intent
            confidence: Confidence score (0-1)
            session_id: Optional session identifier
            response_time_ms: Optional response time in milliseconds

        Returns:
            int: The new chat_messages row ID, or None on failure
        """
        try:
            timestamp = datetime.now().isoformat()
            message_id = None

            with self.lock:
                # Log to database
                message_id = self._log_to_db(
                    timestamp, user_id, session_id, user_message,
                    bot_response, intent, confidence, model_used, response_time_ms
                )

                # Log to file
                self._log_to_file(
                    timestamp, user_id, session_id, user_message,
                    bot_response, intent, confidence, model_used
                )

                # Update intent statistics
                self._update_intent_stats(intent, confidence, timestamp)

                # Update session stats
                if session_id:
                    self._update_session_stats(session_id, user_id, timestamp)

            return message_id
        except Exception as e:
            print(f"[ERROR] Error logging chat: {e}")
            return None

    def _log_to_db(
        self, timestamp, user_id, session_id, user_msg, bot_resp, intent, conf, model_used, resp_time
    ) -> Optional[int]:
        """Log to SQLite database, returns the new row ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO chat_messages
                (timestamp, user_id, session_id, user_message, bot_response, intent, confidence, model_used, response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, user_id, session_id, user_msg, bot_resp, intent, conf, model_used, resp_time))

            row_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return row_id
        except Exception as e:
            print(f"[ERROR] Database log error: {e}")
            return None

    def _log_to_file(self, timestamp, user_id, session_id, user_msg, bot_resp, intent, conf, model_used=None):
        """Log to JSON file"""
        try:
            # Create daily log file
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"chat_{date_str}.log"

            log_entry = {
                "timestamp": timestamp,
                "user_id": user_id,
                "session_id": session_id,
                "user_message": user_msg,
                "bot_response": bot_resp,
                "intent": intent,
                "confidence": conf,
                "model_used": model_used
            }

            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"[ERROR] File log error: {e}")

    def _update_intent_stats(self, intent: str, confidence: float, timestamp: str):
        """Update intent statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO intent_stats (intent, count, avg_confidence, last_used)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(intent) DO UPDATE SET
                    count = count + 1,
                    avg_confidence = (avg_confidence * (count - 1) + ?) / count,
                    last_used = ?
            """, (intent, confidence, timestamp, confidence, timestamp))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR] Intent stats update error: {e}")

    def _update_session_stats(self, session_id: str, user_id: str, timestamp: str):
        """Update session statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if session exists
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE session_id = ?", (session_id,))
            exists = cursor.fetchone()[0] > 0

            if not exists:
                cursor.execute("""
                    INSERT INTO sessions (session_id, user_id, start_time)
                    VALUES (?, ?, ?)
                """, (session_id, user_id, timestamp))
            else:
                cursor.execute("""
                    UPDATE sessions
                    SET message_count = message_count + 1
                    WHERE session_id = ?
                """, (session_id,))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR] Session stats update error: {e}")

    # ========== Retrieval Methods ==========

    def get_user_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get chat history for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM chat_messages
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[ERROR] Error retrieving user history: {e}")
            return []

    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get all messages in a session"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM chat_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[ERROR] Error retrieving session history: {e}")
            return []

    def get_intent_statistics(self) -> List[Dict]:
        """Get statistics for all intents"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT intent, count, avg_confidence, last_used
                FROM intent_stats
                ORDER BY count DESC
            """)

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[ERROR] Error retrieving intent stats: {e}")
            return []

    def get_session_list(self, user_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get list of sessions"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if user_id:
                cursor.execute("""
                    SELECT * FROM sessions
                    WHERE user_id = ?
                    ORDER BY start_time DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM sessions
                    ORDER BY start_time DESC
                    LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[ERROR] Error retrieving sessions: {e}")
            return []

    def get_today_stats(self) -> Dict:
        """Get today's chat statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            today = datetime.now().strftime("%Y-%m-%d")

            # Total messages today
            cursor.execute("""
                SELECT COUNT(*) FROM chat_messages
                WHERE DATE(timestamp) = ?
            """, (today,))
            total_messages = cursor.fetchone()[0]

            # Unique users today
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) FROM chat_messages
                WHERE DATE(timestamp) = ?
            """, (today,))
            unique_users = cursor.fetchone()[0]

            # Average confidence today
            cursor.execute("""
                SELECT AVG(confidence) FROM chat_messages
                WHERE DATE(timestamp) = ?
            """, (today,))
            avg_confidence = cursor.fetchone()[0] or 0

            # Most used intent today
            cursor.execute("""
                SELECT intent, COUNT(*) as count FROM chat_messages
                WHERE DATE(timestamp) = ?
                GROUP BY intent
                ORDER BY count DESC
                LIMIT 1
            """, (today,))
            top_intent = cursor.fetchone()

            conn.close()

            return {
                "date": today,
                "total_messages": total_messages,
                "unique_users": unique_users,
                "average_confidence": round(avg_confidence, 4),
                "top_intent": {
                    "intent": top_intent[0],
                    "count": top_intent[1]
                } if top_intent else None
            }
        except Exception as e:
            print(f"[ERROR] Error getting daily stats: {e}")
            return {}

    def search_logs(self, query: str, limit: int = 20) -> List[Dict]:
        """Search logs by user message or bot response"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            search_term = f"%{query}%"
            cursor.execute("""
                SELECT * FROM chat_messages
                WHERE user_message LIKE ? OR bot_response LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (search_term, search_term, limit))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[ERROR] Error searching logs: {e}")
            return []

    def log_feedback(
        self,
        message_id: Optional[int],
        user_id: Optional[str],
        session_id: Optional[str],
        intent: Optional[str],
        rating: Optional[int],
        helpful: Optional[bool],
        comment: Optional[str],
        suggested_intent: Optional[str],
        user_message: Optional[str] = None,
    ) -> Optional[int]:
        """Log user feedback for a bot response. Returns the new feedback row ID."""
        try:
            timestamp = datetime.now().isoformat()
            helpful_int = int(helpful) if helpful is not None else None

            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO feedback
                    (timestamp, message_id, user_id, session_id, intent, rating, helpful, comment, suggested_intent, user_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (timestamp, message_id, user_id, session_id, intent,
                       rating, helpful_int, comment, suggested_intent, user_message))

                feedback_id = cursor.lastrowid
                conn.commit()
                conn.close()

            return feedback_id
        except Exception as e:
            print(f"[ERROR] Error logging feedback: {e}")
            return None

    def get_feedback_stats(self) -> Dict:
        """Aggregate feedback statistics: overall, per-intent, low-rated, and recent comments."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Overall totals
            cursor.execute("SELECT COUNT(*), AVG(rating), AVG(helpful) FROM feedback")
            row = cursor.fetchone()
            total = row[0] or 0
            avg_rating = round(row[1], 2) if row[1] is not None else None
            helpful_pct = round(row[2] * 100, 1) if row[2] is not None else None

            # Per-intent breakdown
            cursor.execute("""
                SELECT intent,
                       COUNT(*) AS feedback_count,
                       AVG(rating) AS avg_rating,
                       AVG(helpful) AS helpful_pct,
                       SUM(CASE WHEN helpful = 0 THEN 1 ELSE 0 END) AS unhelpful_count
                FROM feedback
                WHERE intent IS NOT NULL
                GROUP BY intent
                ORDER BY feedback_count DESC
            """)
            by_intent = [
                {
                    "intent": r[0],
                    "feedback_count": r[1],
                    "avg_rating": round(r[2], 2) if r[2] is not None else None,
                    "helpful_pct": round(r[3] * 100, 1) if r[3] is not None else None,
                    "unhelpful_count": r[4]
                }
                for r in cursor.fetchall()
            ]

            # Lowest-rated intents (min 3 ratings)
            cursor.execute("""
                SELECT intent, AVG(rating) AS avg_r, COUNT(*) AS cnt
                FROM feedback
                WHERE rating IS NOT NULL AND intent IS NOT NULL
                GROUP BY intent
                HAVING cnt >= 3
                ORDER BY avg_r ASC
                LIMIT 5
            """)
            low_rated = [
                {"intent": r[0], "avg_rating": round(r[1], 2), "count": r[2]}
                for r in cursor.fetchall()
            ]

            # Recent comments
            cursor.execute("""
                SELECT timestamp, intent, rating, helpful, comment, suggested_intent
                FROM feedback
                WHERE comment IS NOT NULL AND TRIM(comment) != ''
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            recent_comments = [
                {
                    "timestamp": r[0],
                    "intent": r[1],
                    "rating": r[2],
                    "helpful": bool(r[3]) if r[3] is not None else None,
                    "comment": r[4],
                    "suggested_intent": r[5]
                }
                for r in cursor.fetchall()
            ]

            conn.close()

            return {
                "total_feedback": total,
                "avg_rating": avg_rating,
                "helpful_pct": helpful_pct,
                "by_intent": by_intent,
                "low_rated_intents": low_rated,
                "recent_comments": recent_comments
            }
        except Exception as e:
            print(f"[ERROR] Error getting feedback stats: {e}")
            return {}

    def get_feedback_entries(
        self,
        limit: int = 100,
        helpful: Optional[bool] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        intent: Optional[str] = None,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None
    ) -> List[Dict]:
        """Return feedback rows joined with their source chat message when available."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            where_clauses = []
            params = []

            if helpful is not None:
                where_clauses.append("f.helpful = ?")
                params.append(int(helpful))
            if user_id:
                where_clauses.append("f.user_id = ?")
                params.append(user_id)
            if session_id:
                where_clauses.append("f.session_id = ?")
                params.append(session_id)
            if intent:
                where_clauses.append("f.intent = ?")
                params.append(intent)
            if min_rating is not None:
                where_clauses.append("f.rating >= ?")
                params.append(min_rating)
            if max_rating is not None:
                where_clauses.append("f.rating <= ?")
                params.append(max_rating)

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            cursor.execute(f"""
                SELECT
                    f.id,
                    f.timestamp,
                    f.message_id,
                    f.user_id,
                    f.session_id,
                    f.intent,
                    f.rating,
                    f.helpful,
                    f.comment,
                    f.suggested_intent,
                    COALESCE(m.user_message, f.user_message) AS user_message,
                    m.bot_response,
                    m.confidence AS message_confidence,
                    m.model_used
                FROM feedback f
                LEFT JOIN chat_messages m ON f.message_id = m.id
                {where_sql}
                ORDER BY f.timestamp DESC
                LIMIT ?
            """, (*params, limit))

            rows = cursor.fetchall()
            conn.close()

            results = []
            for row in rows:
                item = dict(row)
                if item["helpful"] is not None:
                    item["helpful"] = bool(item["helpful"])
                results.append(item)

            return results
        except Exception as e:
            print(f"[ERROR] Error retrieving feedback entries: {e}")
            return []

    def get_fallback_examples(self, limit: int = 100) -> List[Dict]:
        """Get recent fallback user utterances and metadata."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_message, bot_response, timestamp, user_id, session_id, confidence, model_used
                FROM chat_messages
                WHERE intent = 'nlu_fallback'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]
        except Exception as e:
            print(f"[ERROR] Error retrieving fallback examples: {e}")
            return []

    def export_user_data(self, user_id: str) -> str:
        """Export all data for a user as JSON"""
        try:
            history = self.get_user_history(user_id, limit=1000)
            sessions = self.get_session_list(user_id, limit=100)

            export_data = {
                "user_id": user_id,
                "export_date": datetime.now().isoformat(),
                "message_count": len(history),
                "session_count": len(sessions),
                "messages": history,
                "sessions": sessions
            }

            # Save to file
            filename = self.log_dir / f"export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return str(filename)
        except Exception as e:
            print(f"[ERROR] Error exporting user data: {e}")
            return None

    def cleanup_old_logs(self, days: int = 30):
        """Delete logs older than specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = (datetime.now().timestamp() - (days * 86400))

            cursor.execute("""
                DELETE FROM chat_messages
                WHERE strftime('%s', timestamp) < ?
            """, (cutoff_date,))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            print(f"[OK] Deleted {deleted} old log entries")
            return deleted
        except Exception as e:
            print(f"[ERROR] Error cleaning logs: {e}")
            return 0
