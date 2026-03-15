import secrets
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from db import sessions_col
from pymongo.errors import DuplicateKeyError

sessions_bp = Blueprint("sessions", __name__)


def _now():
    return datetime.now(timezone.utc)


@sessions_bp.route("/create_session", methods=["POST"])
def create_session():
    """
    Create a temporary user session and return a token.
    Body: { "username": "Echo", "duration": 30 }
      OR: { "username": "Echo", "session_duration": 30 }  (both accepted)
    Returns: { "token": "...", "username": "...", "expires_at": "..." }
    """
    data     = request.get_json()
    username = data.get("username", "").strip()
    # Accept both field names
    duration = int(data.get("session_duration") or data.get("duration") or 30)

    if not username:
        return jsonify({"error": "username is required"}), 400
    if duration < 5 or duration > 180:
        return jsonify({"error": "duration must be between 5 and 180 minutes"}), 400

    now         = _now()
    session_end = now + timedelta(minutes=duration)
    token       = secrets.token_hex(24)   # 48-char secure random token

    doc = {
        "username":      username,
        "token":         token,
        "session_start": now,
        "session_end":   session_end,
        "expires_at":    session_end,   # TTL index key
    }

    try:
        sessions_col.insert_one(doc)
    except DuplicateKeyError:
        return jsonify({"error": f"Username '{username}' is already in use"}), 409

    return jsonify({
        "status":     "ok",
        "token":      token,
        "username":   username,
        "expires_at": session_end.isoformat(),
    })


@sessions_bp.route("/extend_session", methods=["POST"])
def extend_session():
    """
    Extend session by N minutes.
    Body: { "username": "Echo", "extend_by": 15 }
    """
    data      = request.get_json()
    username  = data.get("username", "").strip()
    extend_by = int(data.get("extend_by", 15))

    result = sessions_col.find_one({"username": username})
    if not result:
        return jsonify({"error": "Session not found"}), 404

    new_end = result["session_end"] + timedelta(minutes=extend_by)
    sessions_col.update_one(
        {"username": username},
        {"$set": {"session_end": new_end, "expires_at": new_end}}
    )
    return jsonify({"status": "extended", "new_session_end": new_end.isoformat()})


@sessions_bp.route("/terminate_session", methods=["POST"])
def terminate_session():
    """
    Immediately end a session and free the username.
    Body: { "username": "Echo" }
    """
    data     = request.get_json()
    username = data.get("username", "").strip()

    sessions_col.delete_one({"username": username})
    return jsonify({"status": "terminated"})


@sessions_bp.route("/session_status/<username>", methods=["GET"])
def session_status(username):
    """Return remaining session time for a username."""
    session = sessions_col.find_one({"username": username})
    if not session:
        return jsonify({"active": False})

    now       = _now()
    remaining = (session["session_end"] - now).total_seconds()
    if remaining <= 0:
        sessions_col.delete_one({"username": username})
        return jsonify({"active": False})

    return jsonify({
        "active":          True,
        "username":        username,
        "remaining_sec":   int(remaining),
        "session_end":     session["session_end"].isoformat(),
    })
