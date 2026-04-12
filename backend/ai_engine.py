"""
AI Engine — Layered emotional support assistant (Ollama + Mistral, local)
Pipeline: Preprocessing → Risk Detection → Emotion Analysis → Prompt Building → Ollama Chat
Uses /api/chat for conversation memory (message history).
"""

import requests
from textblob import TextBlob


OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "mistral"

SYSTEM_PROMPT = """You are a calm, empathetic mental health support assistant named Echo.

STRICT Rules:
- Speak like a caring, warm human friend
- Be emotionally supportive and validate feelings
- Do NOT give medical advice or diagnose anything
- Do NOT sound robotic or clinical
- Keep responses SHORT: 4-5 sentences MAX
- Listen more, lecture less
- Ask gentle follow-up questions
- Use simple, everyday language
- Remember what the user told you earlier in the conversation"""


# ── Layer 1: Preprocessing ───────────────────────────────────────────────────
def preprocess(text):
    """Normalize user input."""
    return text.lower().strip()


# ── Layer 2: Risk Detection (CRITICAL — bypasses AI entirely) ────────────────
DANGER_PHRASES = [
    "suicide", "kill myself", "end my life", "want to die",
    "don't want to live", "no reason to live", "better off dead",
    "self harm", "hurt myself", "cut myself",
]

CRISIS_RESPONSE = (
    "I'm really sorry you're feeling this way. You're not alone. "
    "Please consider reaching out to a trusted person or a helpline:\n\n"
    "📞 iCall: 9152987821 (Mon–Sat, 8am–10pm)\n"
    "📞 Vandrevala Foundation: 1860-2662-345 (24/7)\n\n"
    "You matter, and help is always available. 💚"
)

def detect_risk(text):
    """Scan for crisis indicators. Returns 'high' or 'low'."""
    for phrase in DANGER_PHRASES:
        if phrase in text:
            return "high"
    return "low"


# ── Layer 3: Emotion Detection ───────────────────────────────────────────────
def detect_emotion(text):
    """Use TextBlob sentiment polarity to classify emotion."""
    score = TextBlob(text).sentiment.polarity
    if score < -0.3:
        return "negative"
    elif score > 0.3:
        return "positive"
    else:
        return "neutral"


# ── Layer 4: Ollama Chat API Call (with message history) ─────────────────────
def call_ai(messages):
    """Send conversation history to Ollama /api/chat and return the response."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
            },
            timeout=60,
        )
        data = response.json()
        print(f"[Ollama] Status: {response.status_code}, Keys: {list(data.keys())}")

        if "message" in data:
            return data["message"]["content"]
        elif "error" in data:
            print(f"[Ollama Error] {data['error']}")
            return f"I'm having trouble right now. (Ollama: {data['error']})"
        else:
            print(f"[Ollama] Unexpected response: {data}")
            return "I need a moment. Please try again. 💚"

    except requests.ConnectionError:
        print("[Ollama] Connection failed — is Ollama running?")
        return "I'm having trouble connecting. Please make sure Ollama is running. 💚"
    except Exception as e:
        print(f"[Ollama] Unexpected error: {e}")
        return "Something went wrong. Please try again. 💚"


# ── Final Pipeline ───────────────────────────────────────────────────────────
def ai_response(user_msg, history=None):
    """
    Full AI pipeline:
    1. Preprocess text
    2. Detect risk → if HIGH, return crisis response (NO AI call)
    3. Detect emotion → enrich system prompt
    4. Build message list with history
    5. Call Ollama /api/chat
    6. Return response
    """
    text = preprocess(user_msg)

    # 🚨 CRISIS OVERRIDE — do NOT call AI for high-risk messages
    risk = detect_risk(text)
    if risk == "high":
        return CRISIS_RESPONSE

    # Detect emotion and add context to system prompt
    emotion = detect_emotion(text)
    emotion_hint = ""
    if emotion == "negative":
        emotion_hint = "\nThe user seems upset or stressed. Validate their feelings first, then gently encourage them to share more."
    elif emotion == "positive":
        emotion_hint = "\nThe user seems in a positive mood. Acknowledge and encourage them."

    # Build message list: system + history + current message
    messages = [{"role": "system", "content": SYSTEM_PROMPT + emotion_hint}]

    # Add conversation history (if provided)
    if history:
        for msg in history:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("text", "")})

    # Add current user message
    messages.append({"role": "user", "content": user_msg})

    reply = call_ai(messages)
    return reply.strip()
