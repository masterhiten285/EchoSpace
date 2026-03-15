from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from db import messages_col, sessions_col

messages_bp = Blueprint("messages", __name__)

MESSAGE_TTL_MINUTES = 30  # messages older than this are excluded / deleted


def _now():
    return datetime.now(timezone.utc)


def _session_active(username):
    """Check that the username has a valid active session."""
    session = sessions_col.find_one({"username": username})
    if not session:
        return False
    return session["session_end"] > _now()


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
    return jsonify({"status": "sent"})


@messages_bp.route("/messages/<path:room>", methods=["GET"])
def get_messages(room):
    """
    Return messages from a room within the last 30 minutes.
    Query param: ?limit=50  (default 50)
    """
    limit   = int(request.args.get("limit", 50))
    cutoff  = _now() - timedelta(minutes=MESSAGE_TTL_MINUTES)

    msgs = list(
        messages_col.find(
            {"room": room, "timestamp": {"$gte": cutoff}},
            {"_id": 0, "username": 1, "room": 1, "message": 1, "timestamp": 1}
        ).sort("timestamp", 1).limit(limit)
    )

    # Serialize datetime → ISO string
    for m in msgs:
        m["timestamp"] = m["timestamp"].isoformat()

    return jsonify(msgs)
