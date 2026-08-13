"""
config.py
---------
Central place for all app settings. Keeping these separate from app.py
is a common professional pattern — one file to tweak instead of hunting
through the whole codebase.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API ---
# Locally, the key comes from .env (via load_dotenv above).
# On Streamlit Community Cloud, .env doesn't exist — secrets are set
# in the app's dashboard instead and read through st.secrets. This
# checks st.secrets first, then falls back to the local .env value,
# so the same code works in both places.
try:
    import streamlit as st
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
except Exception:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL_NAME = "llama-3.1-8b-instant"

# --- Database ---
# SQLite needs no server — it's just a local file. Perfect for a
# single-user app like this one, and still a "real" relational database.
DB_PATH = "chat_history.db"
DB_URL = f"sqlite:///{DB_PATH}"

# --- App identity ---
APP_TITLE = "MemoryBot"
APP_ICON = "🧠"
SYSTEM_PROMPT = (
    "You are MemoryBot, a helpful and friendly AI assistant. "
    "You have access to the full conversation history for this session — "
    "use it to give consistent, context-aware answers."
)