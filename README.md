# MindSpace

> A **privacy-first anonymous mental health support platform**.  
> No accounts. No emails. Messages self-delete. Sessions expire.

![Stack](https://img.shields.io/badge/React-19-blue) ![Flask](https://img.shields.io/badge/Flask-3.1-green) ![MongoDB](https://img.shields.io/badge/MongoDB-Atlas%2FLocal-brightgreen)

---

## Quick Start (Run Both Servers)

### 1. Start the Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

### 2. Start the Frontend
```bash
cd frontend
npm install
npm start
# → http://localhost:3000
```

> The frontend auto-falls back to **demo mode** if the backend is not running.

---

## Project Structure

```
dti_project/
├── backend/               ← Python Flask API
│   ├── app.py             ← Entry point
│   ├── db.py              ← MongoDB + TTL indexes
│   ├── cleanup.py         ← Auto-delete scheduler (every 60s)
│   ├── requirements.txt
│   └── routes/
│       ├── alias.py       ← GET  /generate_alias
│       ├── sessions.py    ← POST /create_session, /extend_session, /terminate_session
│       ├── messages.py    ← POST /send_message · GET /messages/<room>
│       └── rooms.py       ← GET  /rooms · POST /create_room
│
└── frontend/              ← React 19 App
    └── src/
        ├── App.js         ← Join screen + main layout
        ├── api.js         ← Axios pointing to :5000
        ├── components/
        │   ├── TopBar.jsx      ← Welcome, search, session timer, avatar
        │   ├── Sidebar.jsx     ← Nav + Help box
        │   ├── RoomsPanel.jsx  ← Room cards with online counts
        │   ├── ChatArea.jsx    ← Messages + input bar (polls every 3s)
        │   └── RightPanel.jsx  ← AI Companion, Mood Check-In, Resources
        └── styles/
            └── *.css
```

---

## Architecture

```
React (port 3000)  ──Axios──▶  Flask (port 5000)  ──PyMongo──▶  MongoDB (port 27017)
```

---

## Privacy Design

| Rule | Detail |
|---|---|
| No email / account | Users only need a temporary username |
| Session TTL | Sessions expire; username becomes reusable |
| Message TTL | All messages auto-delete after **30 minutes** |
| Room TTL | User-created rooms auto-delete after **8 hours** |
| No clinical advice | AI Companion cannot diagnose or prescribe |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Axios, Vanilla CSS (Inter font) |
| Backend | Python Flask 3.1, Flask-CORS, APScheduler |
| Database | MongoDB with TTL indexes |
