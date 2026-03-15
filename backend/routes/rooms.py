from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from db import rooms_col, sessions_col

rooms_bp = Blueprint("rooms", __name__)

ROOM_TTL_HOURS = 8

# Default rooms seeded on first run
DEFAULT_ROOMS = [
    "Academic Stress",
    "Loneliness",
    "Anxiety & Overthinking",
    "Burnout & Motivation",
    "Random Vent Room",
    "Late Night Talks",
]


def _now():
    return datetime.now(timezone.utc)


def _seed_default_rooms():
    """Insert default rooms if they don't exist yet."""
    for name in DEFAULT_ROOMS:
        if not rooms_col.find_one({"room_name": name}):
            now = _now()
            # Default rooms never expire (far future expires_at)
            rooms_col.insert_one({
                "room_name":    name,
                "created_at":  now,
                "expires_at":  now + timedelta(days=3650),  # 10 years
                "is_default":  True,
                "online_count": 0,
            })


@rooms_bp.route("/rooms", methods=["GET"])
def list_rooms():
    """Return all active rooms."""
    rooms = list(
        rooms_col.find(
            {},
            {"_id": 0, "room_name": 1, "created_at": 1, "expires_at": 1,
             "online_count": 1, "is_default": 1}
        ).sort("created_at", 1)
    )
    for r in rooms:
        r["created_at"] = r["created_at"].isoformat()
        r["expires_at"] = r["expires_at"].isoformat()
    return jsonify(rooms)


@rooms_bp.route("/create_room", methods=["POST"])
def create_room():
    """
    Create a new user-generated room (expires after 8 hours).
    Body: { "room_name": "Late Night Talks" }
    """
    data      = request.get_json()
    room_name = data.get("room_name", "").strip()

    if not room_name:
        return jsonify({"error": "room_name is required"}), 400

    if rooms_col.find_one({"room_name": room_name}):
        return jsonify({"error": "A room with this name already exists"}), 409

    now = _now()
    rooms_col.insert_one({
        "room_name":   room_name,
        "created_at":  now,
        "expires_at":  now + timedelta(hours=ROOM_TTL_HOURS),
        "is_default":  False,
        "online_count": 0,
    })
    return jsonify({"status": "created", "room_name": room_name})
