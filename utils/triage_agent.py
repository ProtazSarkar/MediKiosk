"""
Triage Agent & Clinical Gatekeeper (Judge) Engine.
Coordinates:
1. RAG-grounded disease prediction & differential probability scoring.
2. Step-by-step cross-examination questioning to discriminate between hypotheses.
3. Decision Stamp logging (tracking probability evolution turn-by-turn).
4. Clinical Judge evaluation (measuring information completeness and deciding readiness).
5. Comprehensive Handover Report synthesis.
"""

import os
import re
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from utils.rag_engine import get_rag_engine
from utils.medical_kb import CLINICAL_DISEASE_PROFILES

load_dotenv()
logger = logging.getLogger(__name__)

def get_llm_client():
    groq_key = os.getenv("GROQ_API_KEY") or os.getenv("GORQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if groq_key or openai_key.startswith("gsk_"):
        api_key = groq_key or openai_key
        return OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            timeout=5.0,
            max_retries=0
        ), ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    elif openai_key:
        return OpenAI(
            api_key=openai_key,
            timeout=5.0,
            max_retries=0
        ), ["gpt-4o-mini", "gpt-3.5-turbo"]
    return None, []

class ClinicalTriageAgent:
    def __init__(self):
        self.rag = get_rag_engine()

    def process_consultation_turn(self, history, current_state=None):
        """
        Main orchestration loop for each turn of the consultation.
        """
        if current_state is None:
            current_state = {
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
        else:
            current_state.setdefault("uploaded_documents", [])
            current_state.setdefault("past_medical_history", [])
            current_state.setdefault("current_medications", [])
            current_state.setdefault("allergies", [])

        user_messages = [m["content"] for m in history if m["role"] == "user"]
        all_patient_text = " ".join(user_messages)
        if current_state.get("past_medical_history"):
            all_patient_text += " " + " ".join(current_state["past_medical_history"])
        if current_state.get("current_medications"):
            all_patient_text += " " + " ".join(current_state["current_medications"])
        latest_user_message = user_messages[-1] if user_messages else ""

        # Step 1: Query ChromaDB for top clinical candidates
        retrieved_diseases = self.rag.search_relevant_diseases(all_patient_text, n_results=4)

        # Step 2: Attempt LLM reasoning with strict JSON schema
        llm_client, models = get_llm_client()
        result = None

        if llm_client and models:
            result = self._try_llm_reasoning(llm_client, models, history, retrieved_diseases, current_state)

        # Step 3: Fallback to high-fidelity Clinical RAG Reasoning Engine if LLM is unavailable/offline
        if not result:
            result = self._local_clinical_rag_reasoning(history, retrieved_diseases, current_state)

        # Update clinical state
        turn_num = len(current_state["decision_stamps"]) + 1
        decision_stamp = {
            "turn": turn_num,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "hypotheses": result["hypotheses"],
            "rationale": result["stamp_rationale"],
            "differentiating_factor": result.get("differentiating_factor", ""),
            "readiness_at_step": result["readiness_score"]
        }
        current_state["decision_stamps"].append(decision_stamp)
        current_state["current_hypotheses"] = result["hypotheses"]
        current_state["readiness_score"] = result["readiness_score"]
        current_state["decision_ready"] = result["decision_ready"]
        current_state["pertinent_positives"] = list(set(current_state["pertinent_positives"] + result.get("pertinent_positives", [])))
        current_state["pertinent_negatives"] = list(set(current_state["pertinent_negatives"] + result.get("pertinent_negatives", [])))
        current_state["red_flags"] = list(set(current_state["red_flags"] + result.get("red_flags", [])))
        
        if not current_state.get("chief_complaint") and user_messages:
            current_state["chief_complaint"] = user_messages[0]

        # Step 4: If Judge marks decision ready, synthesize the final report
        if current_state["decision_ready"] and not current_state.get("final_report"):
            current_state["final_report"] = self.synthesize_handover_report(current_state, history)

        return {
            "assistant_message": result["assistant_message"],
            "state": current_state
        }

    def _try_llm_reasoning(self, client, models, history, retrieved_diseases, current_state):
        """Invoke LLM with RAG context to compute hypotheses, decision stamps, and gatekeeper score."""
        rag_context = "\n\n".join([
            f"Candidate: {d['name']} (Dept: {d['department']}, ICD-11: {d['icd11']})\n"
            f"Hallmark Symptoms: {d['details'].get('hallmark_symptoms')}\n"
            f"Distinguishing Questions: {d['details'].get('differentiating_questions')}\n"
            f"Pertinent Negatives: {d['details'].get('pertinent_negatives')}\n"
            f"Red Flags: {d['details'].get('red_flags')}"
            for d in retrieved_diseases
        ])

        previous_stamps = json.dumps(current_state.get("decision_stamps", []), indent=2)

        system_prompt = f"""
You are the Lead Clinical Triage & Differential Diagnosis AI in MediKiosk.
Your goal is to actively cross-examine the patient, predict differential disease possibilities with probabilities (summing to 100%), track decision stamps across turns, and act as a clinical Judge to determine if enough evidence exists for a safe pre-consultation summary.

CLINICAL RAG KNOWLEDGE RETRIEVED:
{rag_context}

PREVIOUS DECISION STAMPS:
{previous_stamps}

INSTRUCTIONS:
1. Predict 2-3 most probable diseases with estimated probabilities (e.g. 70%, 20%, 10%).
2. As the chat progresses, detect new symptoms or rule out conditions. Explain how and why probabilities shifted from the previous stamp.
3. Formulate 1-2 empathetic, concise cross-examination questions to discriminate between the top candidates (asking about key differentiating signs or pertinent negatives).
4. Evaluate Judge readiness score (0-100%). Ready when:
   - Chief complaint identified (20%)
   - Duration/onset established (20%)
   - Symptom severity/characterization clear (20%)
   - Differential questions/pertinent negatives answered (20%)
   - Red flags ruled out (20%)
   If readiness >= 80% or turns >= 4, set decision_ready = true.

Respond ONLY with valid JSON in this exact structure:
{{
  "hypotheses": [
    {{"name": "Disease Name", "probability": 70, "department": "Pulmonology", "icd11": "CA20.0"}},
    {{"name": "Competing Disease", "probability": 30, "department": "ENT", "icd11": "CA00"}}
  ],
  "stamp_rationale": "Clear 1-2 sentence medical explanation of why probabilities changed or why new candidate emerged.",
  "differentiating_factor": "Specific factor investigated (e.g., wheezing without fever).",
  "assistant_message": "Your conversational response to the patient, containing brief empathy and your targeted cross-examination questions.",
  "pertinent_positives": ["symptom confirmed present"],
  "pertinent_negatives": ["symptom confirmed absent"],
  "red_flags": [],
  "readiness_score": 60,
  "decision_ready": false
}}
"""
        messages = [{"role": "system", "content": system_prompt}] + history

        for model in models:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.3,
                    response_format={"type": "json_object"} if "llama-3" in model or "gpt" in model else None,
                    max_tokens=650
                )
                content = response.choices[0].message.content.strip()
                # Parse JSON
                data = json.loads(content)
                if "hypotheses" in data and "assistant_message" in data:
                    return data
            except Exception as e:
                logger.error(f"LLM model '{model}' call failed: {e}")
                continue

        return None

    def _local_clinical_rag_reasoning(self, history, retrieved_diseases, current_state):
        """
        High-fidelity deterministic Clinical Decision & Differential Engine.
        Uses RAG disease profiles to score symptoms, compute probabilities,
        generate decision stamps, formulate targeted cross-questions, and score readiness.
        """
        user_messages = [m["content"].lower() for m in history if m["role"] == "user"]
        combined_text = " ".join(user_messages)
        latest_msg = user_messages[-1] if user_messages else ""
        turn_num = len(current_state.get("decision_stamps", [])) + 1

        if not retrieved_diseases:
            retrieved_diseases = self.rag.search_relevant_diseases(combined_text, n_results=4)

        # Candidate scoring based on symptom overlap
        scored_candidates = []
        for d in retrieved_diseases:
            details = d["details"]
            score = 1.0  # Base prior
            matched_positives = []
            matched_negatives = []

            for sym in details.get("hallmark_symptoms", []):
                sym_tokens = [t for t in sym.lower().split() if len(t) > 3]
                if any(tok in combined_text for tok in sym_tokens):
                    score += 2.5
                    matched_positives.append(sym)

            for neg in details.get("pertinent_negatives", []):
                neg_tokens = [t for t in neg.lower().replace("no ", "").split() if len(t) > 3]
                if any(f"no {tok}" in combined_text or f"not {tok}" in combined_text or f"without {tok}" in combined_text for tok in neg_tokens):
                    score += 2.0
                    matched_negatives.append(neg)

            scored_candidates.append({
                "name": d["name"],
                "department": d["department"],
                "icd11": d["icd11"],
                "score": score,
                "details": details,
                "positives": matched_positives,
                "negatives": matched_negatives
            })

        # Sort candidates by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = scored_candidates[:3]

        # Calculate normalized probabilities
        total_score = sum(c["score"] for c in top_candidates) or 1.0
        hypotheses = []
        for c in top_candidates:
            prob = int(round((c["score"] / total_score) * 100))
            hypotheses.append({
                "name": c["name"],
                "probability": prob,
                "department": c["department"],
                "icd11": c["icd11"]
            })

        # Ensure probabilities sum to 100
        if hypotheses:
            prob_diff = 100 - sum(h["probability"] for h in hypotheses)
            hypotheses[0]["probability"] += prob_diff

        # Extract pertinent positives & negatives from recent text
        pertinent_positives = []
        pertinent_negatives = []
        red_flags_found = []

        for kw in ["fever", "cough", "chest pain", "shortness of breath", "headache", "burning", "vomiting", "wheezing", "sore throat", "diarrhea", "pain"]:
            if kw in latest_msg and not any(neg_p in latest_msg for neg_p in [f"no {kw}", f"not {kw}", f"without {kw}"]):
                pertinent_positives.append(kw)
            elif f"no {kw}" in latest_msg or f"not {kw}" in latest_msg or f"without {kw}" in latest_msg:
                pertinent_negatives.append(f"absence of {kw}")

        # Check for red flags
        if any(rf in combined_text for rf in ["crushing chest", "left arm pain", "radiating to jaw", "coughing blood", "difficulty breathing at rest", "worst headache of life", "thunderclap"]):
            red_flags_found.append("CRITICAL: Potential Emergency Presentation Detected")

        # Decision Stamp Rationale
        primary = hypotheses[0] if hypotheses else {"name": "Clinical Evaluation", "probability": 100}
        secondary = hypotheses[1] if len(hypotheses) > 1 else None

        if turn_num == 1:
            rationale = f"Initial presentation points toward {primary['name']} ({primary['probability']}%) based on chief complaint. Differentials include {secondary['name'] if secondary else 'others'}."
            differentiating_factor = "Chief complaint initial cluster"
        else:
            prev_stamp = current_state["decision_stamps"][-1]
            prev_primary = prev_stamp["hypotheses"][0]["name"] if prev_stamp["hypotheses"] else ""
            if prev_primary == primary["name"]:
                rationale = f"Confidence in {primary['name']} solidified to {primary['probability']}% following patient's clinical verification."
            else:
                rationale = f"Hypothesis shifted: {primary['name']} emerged as primary ({primary['probability']}%) displacing {prev_primary} based on discriminating symptoms."
            differentiating_factor = f"Response to cross-question: {latest_msg[:60]}..."

        # Calculate Judge Readiness Score (0-100%)
        readiness = 20  # Base for having chief complaint
        if any(w in combined_text for w in ["day", "week", "month", "hour", "yesterday", "since", "ago"]):
            readiness += 20  # Duration known
        if any(w in combined_text for w in ["mild", "severe", "moderate", "sharp", "dull", "burning", "10", "worst", "scale"]):
            readiness += 20  # Severity/quality known
        if turn_num >= 2 and (pertinent_positives or pertinent_negatives):
            readiness += 20  # Differentiating factors explored
        if turn_num >= 3 or primary["probability"] >= 75:
            readiness += 20  # High discrimination achieved

        readiness = min(readiness, 100)
        decision_ready = readiness >= 80 or turn_num >= 4

        # Formulate assistant question
        if decision_ready:
            assistant_message = (
                f"Thank you for providing those detailed specifics. I have gathered sufficient clinical details "
                f"to establish our preliminary pre-consultation assessment. Our primary diagnostic consideration "
                f"is **{primary['name']}** (Confidence: {primary['probability']}%), with **{secondary['name'] if secondary else 'Alternative'}** as a secondary differential.\n\n"
                f"I have compiled your **Clinical Pre-Consultation Handover Report** below. You may review the decision stamps and download the official doctor summary."
            )
        else:
            # Pick next distinguishing question from primary candidate
            questions = top_candidates[0]["details"].get("differentiating_questions", [])
            q_idx = min(turn_num - 1, len(questions) - 1)
            selected_question = questions[q_idx] if questions else "Could you describe when these symptoms started and if anything makes them better or worse?"

            assistant_message = (
                f"I understand. Based on your symptoms, our clinical reasoning is considering **{primary['name']}** ({primary['probability']}%) "
                f"versus **{secondary['name'] if secondary else 'related conditions'}** ({secondary['probability'] if secondary else '15'}%).\n\n"
                f"To help narrow this down accurately:\n"
                f"👉 **{selected_question}**\n\n"
                f"*(Also, please note approximately how many days you have experienced this.)*"
            )

        return {
            "hypotheses": hypotheses,
            "stamp_rationale": rationale,
            "differentiating_factor": differentiating_factor,
            "assistant_message": assistant_message,
            "pertinent_positives": pertinent_positives,
            "pertinent_negatives": pertinent_negatives,
            "red_flags": red_flags_found,
            "readiness_score": readiness,
            "decision_ready": decision_ready
        }

    def synthesize_handover_report(self, state, history):
        """
        Synthesizes the complete clinical pre-consultation handover report,
        including all decision stamps, probability progression, ICD-11 codes, and triage notes.
        """
        hypotheses = state.get("current_hypotheses", [])
        primary = hypotheses[0] if hypotheses else {"name": "General Medical Concern", "probability": 100, "department": "General Medicine", "icd11": "CA00"}
        secondaries = hypotheses[1:] if len(hypotheses) > 1 else []

        stamps_summary = []
        for s in state.get("decision_stamps", []):
            hyp_str = ", ".join([f"{h['name']} ({h['probability']}%)" for h in s.get("hypotheses", [])])
            stamps_summary.append({
                "step": f"Turn {s.get('turn')}",
                "time": s.get("timestamp"),
                "hypotheses_snapshot": hyp_str,
                "rationale": s.get("rationale"),
                "differentiating_factor": s.get("differentiating_factor")
            })

        report = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chief_complaint": state.get("chief_complaint", "Not specified"),
            "primary_diagnosis": {
                "name": primary.get("name"),
                "confidence": f"{primary.get('probability', 0)}%",
                "department": primary.get("department", "General Medicine"),
                "icd11_code": primary.get("icd11", "Unspecified"),
            },
            "differential_diagnoses": [
                {
                    "name": d.get("name"),
                    "confidence": f"{d.get('probability', 0)}%",
                    "department": d.get("department", "General Medicine"),
                    "icd11_code": d.get("icd11", "Unspecified")
                }
                for d in secondaries
            ],
            "decision_stamps": stamps_summary,
            "uploaded_documents": state.get("uploaded_documents", []),
            "past_medical_history": state.get("past_medical_history", []),
            "current_medications": state.get("current_medications", []),
            "allergies": state.get("allergies", []),
            "pertinent_positives": state.get("pertinent_positives", []),
            "pertinent_negatives": state.get("pertinent_negatives", []),
            "red_flags": state.get("red_flags", []) or ["None identified during intake"],
            "triage_recommendation": f"Refer to {primary.get('department', 'General OPD')} for clinical evaluation and confirmation.",
            "judge_readiness_score": f"{state.get('readiness_score', 0)}%"
        }
        return report

_triage_agent_instance = None

def get_triage_agent():
    global _triage_agent_instance
    if _triage_agent_instance is None:
        _triage_agent_instance = ClinicalTriageAgent()
    return _triage_agent_instance
