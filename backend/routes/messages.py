from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from db import messages_col, sessions_col

messages_bp = Blueprint("messages", __name__)

MESSAGE_TTL_MINUTES = 30  # messages older than this are excluded / deleted


def _now():
    return datetime.now(timezone.utc)


def _utc_iso(dt):
    """Ensure datetime is timezone-aware UTC before ISO conversion."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _session_active(username):
    """Check that the username has a valid active session."""
    session = sessions_col.find_one({"username": username})
    if not session:
        return False
    end = session["session_end"]
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    return end > _now()


@messages_bp.route("/send_message", methods=["POST"])
def send_message():
    """
    Store a chat message.
    Body: { "username": "Echo", "room": "Academic Stress", "message": "..." }
    """
    data     = request.get_json()
    username = data.get("username", "").strip()
    room     = data.get("room", "").strip()
    message  = data.get("message", "").strip()

    if not all([username, room, message]):
        return jsonify({"error": "username, room, and message are required"}), 400

    if not _session_active(username):
        return jsonify({"error": "No active session for this username"}), 401

    now = _now()
    doc = {
        "username":   username,
        "room":       room,
        "message":    message,
        "timestamp":  now,
        "expires_at": now + timedelta(minutes=MESSAGE_TTL_MINUTES),
    }
    messages_col.insert_one(doc)
    print("Message saved:", doc)
    return jsonify({"status": "sent"})


@messages_bp.route("/messages/<path:room>", methods=["GET"])
@messages_bp.route("/get_messages/<path:room>", methods=["GET"])
def get_messages(room):
    """
    Return messages from a room.
    """
    msgs = list(messages_col.find({"room": room}, {"_id": 0}))

    # Serialize datetime → UTC ISO string (with +00:00 so JS treats as UTC)
    for m in msgs:
        if "timestamp" in m and isinstance(m["timestamp"], datetime):
            m["timestamp"] = _utc_iso(m["timestamp"])
        if "expires_at" in m:
            del m["expires_at"]

    return jsonify(msgs)


