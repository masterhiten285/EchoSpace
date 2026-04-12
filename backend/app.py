"""
EchoSpace — Flask Backend Entry Point
======================================
Runs on http://localhost:5000
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

from routes.alias    import alias_bp
from routes.sessions import sessions_bp
from routes.messages import messages_bp
from routes.rooms    import rooms_bp, _seed_default_rooms
from cleanup         import start_cleanup_scheduler
from ai_engine       import ai_response

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])   # Allow React dev server

# ── Register Blueprints ───────────────────────────────────────────────────────
app.register_blueprint(alias_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(messages_bp)
app.register_blueprint(rooms_bp)

# ── Health check ──────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "EchoSpace API"}

# ── AI Chat endpoint ─────────────────────────────────────────────────────────
@app.route("/ai_chat", methods=["POST"])
def ai_chat():
    """Process user message through the AI engine pipeline."""
    data    = request.get_json()
    msg     = data.get("message", "").strip()
    history = data.get("history", [])   # previous messages for context

    if not msg:
        return jsonify({"error": "message is required"}), 400

    try:
        reply = ai_response(msg, history=history)
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"[AI Error] {e}")
        return jsonify({
            "reply": "I'm here for you, but I'm having trouble connecting right now. Please try again in a moment. 💚"
        })

# ── Startup tasks ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _seed_default_rooms()          # Insert default rooms if not present
    start_cleanup_scheduler()      # Start background cleanup every 60 s
    app.run(debug=True, port=5000)

