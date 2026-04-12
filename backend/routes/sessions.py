import secrets
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from db import sessions_col
from pymongo.errors import DuplicateKeyError

sessions_bp = Blueprint("sessions", __name__)


def _now():
    return datetime.now(timezone.utc)


def _utc_iso(dt):
    """Ensure a datetime is timezone-aware UTC before converting to ISO string.
    PyMongo returns naive datetimes from MongoDB; without +00:00 suffix,
    JavaScript's new Date() interprets them as local time (wrong!)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


@sessions_bp.route("/create_session", methods=["POST"])
def create_session():
    """
    Create a temporary user session and return a token.
    Body: { "username": "Echo", "duration": 30 }
      OR: { "username": "Echo", "session_duration": 30 }
    """
    data     = request.get_json()
    username = data.get("username", "").strip()
    duration = int(data.get("session_duration") or data.get("duration") or 30)

    if not username:
        return jsonify({"error": "username is required"}), 400
    if duration < 5 or duration > 180:
        return jsonify({"error": "duration must be between 5 and 180 minutes"}), 400

    now         = _now()
    session_end = now + timedelta(minutes=duration)
    token       = secrets.token_hex(24)

    doc = {
        "username":      username,
        "token":         token,
        "session_start": now,
        "session_end":   session_end,
        "expires_at":    session_end,
        "current_room":  None,
    }

    try:
        sessions_col.insert_one(doc)
    except DuplicateKeyError:
        return jsonify({"error": f"Username '{username}' is already in use"}), 409

    return jsonify({
        "status":     "ok",
        "token":      token,
        "username":   username,
        "expires_at": _utc_iso(session_end),
    })


@sessions_bp.route("/extend_session", methods=["POST"])
def extend_session():
    """
    Extend session by N minutes.
    Body: { "username": "Echo", "extend_by": 15 }
      OR: { "token": "...", "extra_time": 15 }
    """
    data      = request.get_json()
    username  = data.get("username", "").strip()
    token     = data.get("token", "").strip()
    extend_by = int(data.get("extend_by") or data.get("extra_time") or 15)

    # Find session by username or token
    query = {"username": username} if username else {"token": token}
    session = sessions_col.find_one(query)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    # Ensure timezone-aware before arithmetic
    old_end = session["session_end"]
    if old_end.tzinfo is None:
        old_end = old_end.replace(tzinfo=timezone.utc)

    new_end = old_end + timedelta(minutes=extend_by)
    sessions_col.update_one(
        {"_id": session["_id"]},
        {"$set": {"session_end": new_end, "expires_at": new_end}}
    )
    print(f"[Session] Extended {session['username']} by {extend_by}min → {_utc_iso(new_end)}")
    return jsonify({"status": "extended", "new_session_end": _utc_iso(new_end)})


@sessions_bp.route("/terminate_session", methods=["POST"])
def terminate_session():
    """Immediately end a session and free the username."""
    data     = request.get_json()
    username = data.get("username", "").strip()
    sessions_col.delete_one({"username": username})
    return jsonify({"status": "terminated"})


@sessions_bp.route("/join_room", methods=["POST"])
def join_room():
    """
    Track which room the user is currently in.
    Body: { "username": "Echo", "room": "Academic Stress" }
    """
    data     = request.get_json()
    username = data.get("username", "").strip()
    room     = data.get("room", "").strip()
    sessions_col.update_one(
        {"username": username},
        {"$set": {"current_room": room}}
    )
    return jsonify({"status": "ok"})


@sessions_bp.route("/room_online/<path:room>", methods=["GET"])
def room_online(room):
    """Return count of active users in a room."""
    now = _now()
    count = sessions_col.count_documents({
        "current_room": room,
        "session_end": {"$gt": now}
    })
    return jsonify({"room": room, "online": count})


@sessions_bp.route("/session_status/<username>", methods=["GET"])
def session_status(username):
    """Return remaining session time for a username."""
    session = sessions_col.find_one({"username": username})
    if not session:
        return jsonify({"active": False})

    now       = _now()
    end       = session["session_end"]
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    remaining = (end - now).total_seconds()
    if remaining <= 0:
        sessions_col.delete_one({"username": username})
        return jsonify({"active": False})

    return jsonify({
        "active":          True,
        "username":        username,
        "remaining_sec":   int(remaining),
        "session_end":     _utc_iso(end),
    })


