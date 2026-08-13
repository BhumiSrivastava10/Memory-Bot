"""
app.py
------
MemoryBot — an AI chatbot with real, persistent memory.

Unlike a basic chatbot that forgets everything when the app restarts,
MemoryBot stores every conversation in a SQLite database. Close the app,
restart your computer, come back tomorrow — your chat history is still
there.

Run with:  streamlit run app.py
"""

import logging

import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from config import GROQ_API_KEY, MODEL_NAME, APP_TITLE, APP_ICON, SYSTEM_PROMPT
from database import get_history, list_sessions, delete_session, message_count, new_session_id

# ---------------------------------------------------------------------
# Logging — instead of silent failures, problems get written to the
# console with a timestamp. Standard practice in real applications.
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="centered")

# ---------------------------------------------------------------------
# Styling — a single, fixed dark theme. Colors are plain hex values,
# no toggle, no light mode. Kept simple on purpose.
# ---------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        .stApp { background-color: #0F1117; color: #E5E7EB; }
        .block-container { padding-top: 2.5rem; max-width: 760px; }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1A1D27;
            border-right: 1px solid #2D3140;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 8px;
            border: 1px solid #2D3140;
            background-color: #1A1D27;
            color: #E5E7EB;
            font-weight: 500;
        }
        .stButton > button:hover {
            border-color: #818CF8;
            color: #818CF8;
        }

        /* Header */
        .mb-header { display: flex; align-items: center; gap: 14px; }
        .mb-logo {
            width: 46px; height: 46px; border-radius: 12px;
            background: linear-gradient(135deg, #6366F1, #818CF8);
            display: flex; align-items: center; justify-content: center;
            font-size: 22px;
        }
        .mb-title { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 1.7rem; color: #F1F5F9; margin: 0; }
        .mb-subtitle { color: #94A3B8; font-size: 0.85rem; margin: 0; }
        .mb-badge {
            display: inline-flex; align-items: center; gap: 6px;
            background: #0F2A21; color: #6EE7B7; border: 1px solid #1E4A3A;
            padding: 3px 10px; border-radius: 999px; font-size: 0.75rem;
            font-weight: 600; margin-top: 12px;
        }
        .mb-badge .dot { width: 6px; height: 6px; border-radius: 50%; background: #6EE7B7; }

        /* Chat bubbles */
        div[data-testid="stChatMessage"] {
            border-radius: 14px;
            padding: 10px 14px;
            margin-bottom: 4px;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
            background: #262B45;
            border: 1px solid #3F4570;
        }
        div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {
            background: #1A1D27;
            border: 1px solid #2D3140;
        }

        /* Chat input */
        div[data-testid="stChatInput"] {
            border-radius: 12px;
            background-color: #1A1D27;
            border: 1px solid #2D3140;
        }

        .session-caption { color: #64748B; font-size: 0.75rem; margin-top: -6px; margin-bottom: 6px; }
        hr { border-color: #2D3140 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Guard clause: fail loudly and clearly if the API key is missing,
# instead of letting a cryptic error happen later.
# ---------------------------------------------------------------------
if not GROQ_API_KEY:
    st.error(
        "No GROQ_API_KEY found. Create a `.env` file in this folder with:\n\n"
        "`GROQ_API_KEY=your_key_here`"
    )
    st.stop()


# ---------------------------------------------------------------------
# Build the LLM + prompt + chain (cached so it's built once, not on
# every single rerun — Streamlit reruns the whole script on every
# interaction, so caching expensive setup matters).
# ---------------------------------------------------------------------
@st.cache_resource
def build_chain():
    llm = ChatGroq(model=MODEL_NAME, groq_api_key=GROQ_API_KEY)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    chain = prompt | llm
    return RunnableWithMessageHistory(
        chain,
        get_history,
        input_messages_key="input",
        history_messages_key="history",
    )


chatbot = build_chain()


# ---------------------------------------------------------------------
# Sidebar — session management, backed by the database
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        "<p style='font-family:Sora,sans-serif; font-weight:700; font-size:1.15rem; "
        "color:#F1F5F9; margin-bottom:4px;'>💬 Conversations</p>",
        unsafe_allow_html=True,
    )

    if "session_id" not in st.session_state:
        existing = list_sessions()
        st.session_state.session_id = existing[0] if existing else new_session_id()

    if st.button("➕ New chat", use_container_width=True):
        st.session_state.session_id = new_session_id()
        st.rerun()

    st.divider()

    sessions = list_sessions()
    if st.session_state.session_id not in sessions:
        sessions = [st.session_state.session_id] + sessions

    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = None

    for sid in sessions:
        count = message_count(sid)
        label = f"{'🟢 ' if sid == st.session_state.session_id else ''}{sid}"

        # If this session is pending deletion, show a Yes/Cancel prompt
        # instead of the normal row — this is the safety net.
        if st.session_state.confirm_delete == sid:
            st.warning(f"Delete **{sid}**? This can't be undone.")
            yes_col, no_col = st.columns(2)
            with yes_col:
                if st.button("✅ Yes, delete", key=f"confirm-{sid}", use_container_width=True):
                    delete_session(sid)
                    st.session_state.confirm_delete = None
                    if sid == st.session_state.session_id:
                        remaining = [s for s in sessions if s != sid]
                        st.session_state.session_id = remaining[0] if remaining else new_session_id()
                    st.rerun()
            with no_col:
                if st.button("Cancel", key=f"cancel-{sid}", use_container_width=True):
                    st.session_state.confirm_delete = None
                    st.rerun()
            continue

        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(label, key=f"select-{sid}", use_container_width=True):
                st.session_state.session_id = sid
                st.rerun()
            st.markdown(
                f"<div class='session-caption'>{count} messages</div>",
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("🗑️", key=f"delete-{sid}"):
                st.session_state.confirm_delete = sid
                st.rerun()

    st.divider()
    st.caption("Chat history is stored permanently in `chat_history.db` (SQLite).")


# ---------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------
st.markdown(
    f"""
    <div class="mb-header">
        <div class="mb-logo">{APP_ICON}</div>
        <div>
            <p class="mb-title">{APP_TITLE}</p>
            <p class="mb-subtitle">AI assistant with persistent memory</p>
        </div>
    </div>
    <div class="mb-badge"><span class="dot"></span>Saved to database</div>
    """,
    unsafe_allow_html=True,
)
st.caption(f"Session: `{st.session_state.session_id}`")

history = get_history(st.session_state.session_id)

for msg in history.messages:
    role = "user" if msg.type == "human" else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

user_input = st.chat_input("Message MemoryBot...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    try:
        with st.spinner("Thinking..."):
            response = chatbot.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": st.session_state.session_id}},
            )
        with st.chat_message("assistant"):
            st.markdown(response.content)
    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        st.error("Something went wrong talking to the model. Check your API key and connection.")
