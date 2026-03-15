from pymongo import MongoClient, ASCENDING
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME   = os.environ.get("DB_NAME", "mindspace")

client = MongoClient(MONGO_URI)
db     = client[DB_NAME]

# ── Collections ──────────────────────────────────────────────────────────────
sessions_col = db["sessions"]
messages_col = db["messages"]
rooms_col    = db["rooms"]

# ── TTL Indexes (MongoDB auto-deletes docs when expires_at is reached) ────────
sessions_col.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
messages_col.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
rooms_col.create_index(   [("expires_at", ASCENDING)], expireAfterSeconds=0)

# ── Unique index: no two active sessions share a username ─────────────────────
sessions_col.create_index([("username", ASCENDING)], unique=True, sparse=True)
