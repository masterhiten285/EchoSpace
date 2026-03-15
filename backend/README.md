# MindSpace Backend

> Python Flask REST API + MongoDB for the MindSpace anonymous mental health support platform.

## Quick Start

### 1. Prerequisites
- Python 3.10+
- MongoDB running locally on port 27017 (or provide a URI via `.env`)

### 2. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. (Optional) Configure environment
Create a `.env` file in `backend/`:
```
MONGO_URI=mongodb://localhost:27017/
DB_NAME=mindspace
```

### 4. Run the server
```bash
python app.py
```

Server starts at **http://localhost:5000**

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/generate_alias` | Get a random anonymous username |
| `POST` | `/create_session` | Start a timed user session |
| `GET` | `/session_status/<username>` | Check remaining session time |
| `POST` | `/extend_session` | Add more time to a session |
| `POST` | `/terminate_session` | End a session immediately |
| `POST` | `/send_message` | Send a chat message to a room |
| `GET` | `/messages/<room>` | Get last 30 min of messages |
| `GET` | `/rooms` | List all active rooms |
| `POST` | `/create_room` | Create a new room (8-hr TTL) |

---

## Architecture

```
backend/
├── app.py          ← Flask app, blueprint registration, startup
├── db.py           ← MongoDB connection + TTL index setup
├── cleanup.py      ← APScheduler background cleanup every 60s
├── requirements.txt
└── routes/
    ├── alias.py    ← GET /generate_alias
    ├── sessions.py ← Session create/extend/terminate
    ├── messages.py ← Send + fetch messages (30-min window)
    └── rooms.py    ← List + create rooms
```

## Auto-Cleanup Rules

| Data | Expires After |
|---|---|
| Messages | 30 minutes |
| Sessions | Duration chosen by user |
| User-created rooms | 8 hours |
| Default rooms | Never |

Cleanup runs via **MongoDB TTL indexes** (passive) + **APScheduler** every 60s (active).
