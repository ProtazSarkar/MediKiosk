import os
import json
import uuid
import logging
from flask import Flask, render_template, request, jsonify, send_file, session
from dotenv import load_dotenv
from utils.triage_agent import get_triage_agent
from utils.pdf_generator import generate_pdf_summary
from utils.document_parser import get_prescription_parser

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "medi_kiosk_secret_key_2026")

STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

def get_log_path(user_id):
    return os.path.join(STORAGE_DIR, f"{user_id}.json")

def read_session_data(user_id):
    log_path = get_log_path(user_id)
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Legacy structure
                    return {"history": data, "clinical_state": None}
                return data
        except Exception as e:
            logger.error(f"Error reading session data for {user_id}: {e}")
    return {"history": [], "clinical_state": None}

def save_session_data(user_id, history, clinical_state):
    log_path = get_log_path(user_id)
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({
                "history": history,
                "clinical_state": clinical_state
            }, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving session data for {user_id}: {e}")

@app.route("/")
def index():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    user_id = session["user_id"]
    log_path = get_log_path(user_id)
    if not os.path.exists(log_path):
        save_session_data(user_id, [], None)
    return render_template("index.html")

@app.route("/history", methods=["GET"])
def history():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "history": [],
            "message_count": 0,
            "clinical_state": None,
            "decision_ready": False,
            "pdf_url": None
        })

    session_data = read_session_data(user_id)
    history = session_data.get("history", [])
    state = session_data.get("clinical_state")
    decision_ready = state.get("decision_ready", False) if state else False
    pdf_url = f"/download_pdf/{user_id}" if decision_ready else None

    return jsonify({
        "history": history,
        "message_count": len(history),
        "clinical_state": state,
        "decision_ready": decision_ready,
        "pdf_url": pdf_url
    })

@app.route("/upload_document", methods=["POST"])
def upload_document():
    user_id = session.get("user_id")
    if not user_id:
        session["user_id"] = str(uuid.uuid4())
        user_id = session["user_id"]

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "No file selected"}), 400

    parser = get_prescription_parser()
    parse_result = parser.parse_document(file, file.filename)

    if not parse_result.get("success"):
        return jsonify({"error": parse_result.get("error", "Failed to parse document")}), 400

    session_data = read_session_data(user_id)
    history = session_data.get("history", [])
    state = session_data.get("clinical_state") or {
        "decision_stamps": [],
        "current_hypotheses": [],
        "readiness_score": 0,
        "decision_ready": False,
        "pertinent_positives": [],
        "pertinent_negatives": [],
        "red_flags": [],
        "chief_complaint": "",
        "duration": "",
        "uploaded_documents": [],
        "past_medical_history": [],
        "current_medications": [],
        "allergies": [],
        "final_report": None
    }

    state.setdefault("uploaded_documents", [])
    state.setdefault("past_medical_history", [])
    state.setdefault("current_medications", [])
    state.setdefault("allergies", [])

    # Append to state
    state["uploaded_documents"].append(parse_result)
    if parse_result.get("diagnoses"):
        state["past_medical_history"].extend(parse_result["diagnoses"])
    if parse_result.get("medications"):
        state["current_medications"].extend(parse_result["medications"])
    if parse_result.get("allergies"):
        state["allergies"].extend(parse_result["allergies"])

    # Boost judge readiness score because prior records are documented
    state["readiness_score"] = min(state.get("readiness_score", 0) + 20, 90)

    # Clean duplicates
    state["past_medical_history"] = list(dict.fromkeys(state["past_medical_history"]))
    state["current_medications"] = list(dict.fromkeys(state["current_medications"]))
    state["allergies"] = list(dict.fromkeys(state["allergies"]))

    # Add confirmation message to chat history
    meds_str = ", ".join(parse_result.get("medications", [])) or "None identified"
    diags_str = ", ".join(parse_result.get("diagnoses", [])) or "None identified"
    allergies_str = ", ".join(parse_result.get("allergies", [])) or "None noted"

    assistant_msg = (
        f"📄 **Prior Medical Record / Prescription Digitized (`{parse_result.get('file_name')}`)**\n\n"
        f"I have reviewed and incorporated your document into your clinical record:\n"
        f"• **Prior Diagnoses:** {diags_str}\n"
        f"• **Active Medications:** {meds_str}\n"
        f"• **Allergies:** {allergies_str}\n\n"
        f"Please describe what new symptoms or health concerns brought you to the clinic today, and I will assist with preliminary evaluation."
    )
    history.append({"role": "assistant", "content": assistant_msg})

    save_session_data(user_id, history, state)

    return jsonify({
        "status": "success",
        "extracted": parse_result,
        "assistant_message": assistant_msg,
        "clinical_state": state
    })

@app.route("/chat", methods=["POST"])
def chat():
    user_id = session.get("user_id")
    if not user_id:
        session["user_id"] = str(uuid.uuid4())
        user_id = session["user_id"]

    user_message = request.json.get("message", "").strip() if request.is_json else ""
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    session_data = read_session_data(user_id)
    history = session_data.get("history", [])
    clinical_state = session_data.get("clinical_state")

    # Append user message
    history.append({"role": "user", "content": user_message})

    # Execute Clinical Triage Agent with RAG and Judge Gatekeeper
    triage_agent = get_triage_agent()
    result = triage_agent.process_consultation_turn(history, clinical_state)

    assistant_response = result["assistant_message"]
    updated_state = result["state"]

    # Append assistant message
    history.append({"role": "assistant", "content": assistant_response})

    # Check if Judge marked decision ready
    decision_ready = updated_state.get("decision_ready", False)
    pdf_url = None

    if decision_ready:
        generate_pdf_summary(user_id, history, updated_state)
        pdf_url = f"/download_pdf/{user_id}"

    # Persist updated session
    save_session_data(user_id, history, updated_state)

    return jsonify({
        "response": assistant_response,
        "message_count": len(history),
        "clinical_state": updated_state,
        "decision_ready": decision_ready,
        "pdf_url": pdf_url
    })

@app.route("/generate_report", methods=["POST"])
def generate_report():
    """Manual trigger to force report generation even if turns are few."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "No active session"}), 400

    session_data = read_session_data(user_id)
    history = session_data.get("history", [])
    state = session_data.get("clinical_state") or {}

    triage_agent = get_triage_agent()
    state["decision_ready"] = True
    state["readiness_score"] = 100
    state["final_report"] = triage_agent.synthesize_handover_report(state, history)

    save_session_data(user_id, history, state)
    generate_pdf_summary(user_id, history, state)

    return jsonify({
        "status": "success",
        "clinical_state": state,
        "pdf_url": f"/download_pdf/{user_id}"
    })

@app.route("/reset", methods=["POST"])
def reset():
    new_user_id = str(uuid.uuid4())
    session["user_id"] = new_user_id
    save_session_data(new_user_id, [], None)
    return jsonify({"status": "success", "user_id": new_user_id})

@app.route("/download_pdf/<user_id>")
def download_pdf(user_id):
    pdf_path = os.path.join(STORAGE_DIR, f"{user_id}.pdf")
    if not os.path.exists(pdf_path):
        session_data = read_session_data(user_id)
        history = session_data.get("history", [])
        state = session_data.get("clinical_state")
        if history:
            generate_pdf_summary(user_id, history, state)
        else:
            return "PDF not found", 404

    if os.path.exists(pdf_path):
        return send_file(
            pdf_path,
            as_attachment=True,
            mimetype="application/pdf",
            download_name=f"MediKiosk_Clinical_Handover_{user_id[:8]}.pdf"
        )
    return "PDF not found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)
