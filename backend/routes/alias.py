import random
from flask import Blueprint, jsonify

alias_bp = Blueprint("alias", __name__)

ADJECTIVES = [
    "Echo", "River", "Sky", "Leaf", "Storm", "Mist", "Dusk",
    "Nova", "Sage", "Fern", "Cloud", "Ash", "Brook", "Ember",
    "Gale", "Dawn", "Vale", "Reed", "Lark", "Moon"
]

@alias_bp.route("/generate_alias", methods=["GET"])
def generate_alias():
    """Return a random anonymous username like Echo_381."""
    name   = random.choice(ADJECTIVES)
    number = random.randint(10, 999)
    return jsonify({"username": f"{name}_{number}"})
