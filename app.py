import os
import json
import uuid
import logging
from flask import Flask, render_template, request, jsonify, send_file, session
from dotenv import load_dotenv
from utils.chat_handler import get_llm_response
from utils.pdf_generator import generate_pdf_summary

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

def get_log_path(user_id):
    return os.path.join(STORAGE_DIR, f"{user_id}.json")

def read_history(user_id):
    log_path = get_log_path(user_id)
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading history for {user_id}: {e}")
    return []

def save_history(user_id, history):
    log_path = get_log_path(user_id)
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving history for {user_id}: {e}")

@app.route("/")
def index():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    user_id = session["user_id"]
    log_path = get_log_path(user_id)
    if not os.path.exists(log_path):
        save_history(user_id, [])
    return render_template("index.html")

@app.route("/history", methods=["GET"])
def history():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"history": [], "message_count": 0, "limit_reached": False, "pdf_url": None})
    
    history = read_history(user_id)
    limit_reached = len(history) >= 10
    pdf_url = f"/download_pdf/{user_id}" if limit_reached else None
    return jsonify({
        "history": history,
        "message_count": len(history),
        "limit_reached": limit_reached,
        "pdf_url": pdf_url
    })

@app.route("/chat", methods=["POST"])
def chat():
    user_id = session.get("user_id")
    if not user_id:
        # Re-initialize session if expired
        session["user_id"] = str(uuid.uuid4())
        user_id = session["user_id"]

    user_message = request.json.get("message", "").strip() if request.is_json else ""
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    history = read_history(user_id)

    # Enforce limit of 10 total messages (5 user + 5 assistant turns)
    if len(history) >= 10:
        pdf_path = os.path.join(STORAGE_DIR, f"{user_id}.pdf")
        if not os.path.exists(pdf_path):
            generate_pdf_summary(user_id, history)
        return jsonify({
            "response": "Chat limit reached. Please download your consultation summary report below.",
            "message_count": len(history),
            "limit_reached": True,
            "pdf_url": f"/download_pdf/{user_id}"
        })

    # Append user message
    history.append({"role": "user", "content": user_message})

    # Get assistant response
    assistant_response = get_llm_response(history)

    # Append assistant response
    history.append({"role": "assistant", "content": assistant_response})

    # Save to storage
    save_history(user_id, history)

    limit_reached = len(history) >= 10
    pdf_url = None
    if limit_reached:
        generate_pdf_summary(user_id, history)
        pdf_url = f"/download_pdf/{user_id}"

    return jsonify({
        "response": assistant_response,
        "message_count": len(history),
        "limit_reached": limit_reached,
        "pdf_url": pdf_url
    })

@app.route("/reset", methods=["POST"])
def reset():
    new_user_id = str(uuid.uuid4())
    session["user_id"] = new_user_id
    save_history(new_user_id, [])
    return jsonify({"status": "success", "user_id": new_user_id})

@app.route("/download_pdf/<user_id>")
def download_pdf(user_id):
    pdf_path = os.path.join(STORAGE_DIR, f"{user_id}.pdf")
    if not os.path.exists(pdf_path):
        history = read_history(user_id)
        if history:
            generate_pdf_summary(user_id, history)
        else:
            return "PDF not found", 404

    if os.path.exists(pdf_path):
        return send_file(
            pdf_path,
            as_attachment=True,
            mimetype="application/pdf",
            download_name=f"MediKiosk_Summary_{user_id[:8]}.pdf"
        )
    return "PDF not found", 404

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)