"""
database.py
-----------
All database logic lives here, separate from the UI and the AI logic.
This separation is called "separation of concerns" — it makes the
project easier to read, test, and extend (e.g. swapping SQLite for
Postgres later would only mean touching this one file).

We use LangChain's SQLChatMessageHistory, which stores every message
in a real SQLite table called "message_store". SQLite ships built
into Python — no server or extra installs needed.
"""

import sqlite3
from datetime import datetime

from langchain_community.chat_message_histories import SQLChatMessageHistory

from config import DB_URL, DB_PATH


def get_history(session_id: str) -> SQLChatMessageHistory:
    """
    Return the persistent chat history object for a given session.
    Reading/writing to it automatically reads/writes rows in SQLite.
    """
    return SQLChatMessageHistory(session_id=session_id, connection=DB_URL)


def list_sessions() -> list[str]:
    """
    Return every distinct session_id currently stored in the database,
    most recently active first. Used to populate the sidebar so past
    conversations can be reopened after restarting the app.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT session_id, MAX(id) as last_id
            FROM message_store
            GROUP BY session_id
            ORDER BY last_id DESC
            """
        )
        sessions = [row[0] for row in cur.fetchall()]
        conn.close()
        return sessions
    except sqlite3.OperationalError:
        # Table doesn't exist yet — happens on very first run
        # before any message has ever been sent.
        return []


def delete_session(session_id: str) -> None:
    """Permanently delete one conversation's history from the database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM message_store WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def message_count(session_id: str) -> int:
    """How many messages exist for a session — shown in the UI."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM message_store WHERE session_id = ?",
            (session_id,),
        )
        count = cur.fetchone()[0]
        conn.close()
        return count
    except sqlite3.OperationalError:
        return 0


def new_session_id() -> str:
    """Generate a friendly, unique session name based on the current time."""
    return f"chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
