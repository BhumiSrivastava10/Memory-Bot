# 🧠 MemoryBot — AI Chatbot with Persistent Memory

A conversational AI assistant that remembers you — permanently. Unlike
basic chatbot demos that lose all context on restart, MemoryBot stores
every conversation in a real SQLite database, supports multiple
named chat sessions, and lets you revisit or delete past conversations.

## 🚀 Live Demo

https://memory-bot-4yde6qykmmdn8fwmxqvfqi.streamlit.app/

## Features

- 🗄️ **Persistent memory** — conversations are stored in a SQLite database and survive app restarts
- 💬 **Multi-session support** — start new chats, switch between them, and delete old ones from the sidebar
- ⚡ **Fast inference** — powered by Groq's hosted Llama 3.1 model
- 🎨 **Custom UI** — clean, dark-themed chat interface built with Streamlit
- 🛡️ **Error handling & logging** — clear errors instead of crashes, timestamped logs for debugging

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Orchestration | LangChain (`RunnableWithMessageHistory`) |
| LLM | Llama 3.1 8B via Groq API |
| Database | SQLite (via LangChain's `SQLChatMessageHistory`) |

## Project Structure

```
memory-chatbot-v2/
├── app.py             # Main Streamlit app — UI and chat logic
├── database.py         # All database (SQLite) logic
├── config.py            # App settings and constants
├── requirements.txt     # Python dependencies
├── .env.example          # Template for your API key
└── .gitignore
```

Splitting the code this way (UI / database / config) is a standard
professional pattern — it keeps each file focused on one job, and
makes the project easy to extend later (e.g. swapping SQLite for
Postgres would only mean editing `database.py`).

## Prerequisites (install before running)

1. **Python 3.9+** — check with `python --version`
2. **A free Groq API key** — [console.groq.com](https://console.groq.com) → API Keys → Create API Key
3. That's it — SQLite needs no install, it's built into Python.

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
cp .env.example .env
# then open .env and paste your real key in place of your_api_key_here

# 4. Run the app
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

## How the memory works

Every message you send is saved as a row in `chat_history.db`
(created automatically on first run), tagged with a `session_id`.
When you send a new message:

1. LangChain fetches all past messages for the current session from SQLite
2. They're inserted into the prompt so the model has full context
3. Your new message + the model's reply are both saved back to the database

Because it's a real file-based database, your conversations are
still there the next time you open the app — even after a restart.

## Possible Next Steps

- Deploy to Streamlit Community Cloud for a live demo link
- Add user authentication so multiple people can use it with separate histories
- Swap SQLite for Postgres/Supabase for a cloud-hosted database
- Add streaming responses (token-by-token) instead of waiting for the full reply
