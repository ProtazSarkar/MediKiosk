import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)

def get_client_and_models():
    """
    Detect API key type (Groq vs xAI vs OpenAI) and return appropriate client and models.
    """
    groq_key = os.getenv("GROQ_API_KEY") or os.getenv("GORQ_API_KEY") or os.getenv("GORK_API_KRY")
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    # If key starts with gsk_ or groq_key is set, use Groq API
    if groq_key or openai_key.startswith("gsk_"):
        api_key = groq_key or openai_key
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        return client, ["openai/gpt-oss-20b", "llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    elif openai_key:
        client = OpenAI(api_key=openai_key)
        return client, ["gpt-3.5-turbo", "gpt-4o-mini"]
    else:
        return None, []

def get_llm_response(history):
    system_prompt = {
        "role": "system",
        "content": (
            "You are a helpful, empathetic, and professional AI Medical Kiosk Assistant. "
            "Provide clear, concise, and preliminary medical guidance based on the patient's described symptoms. "
            "Keep your advice grounded, ask clarifying symptom questions when necessary, "
            "and remind the patient to consult a qualified physician for actual diagnosis."
        )
    }
    
    messages = [system_prompt] + history

    client, candidate_models = get_client_and_models()

    if not client or not candidate_models:
        logger.warning("No valid API key configured. Utilizing fallback response.")
        return generate_fallback_response(history)

    for model in candidate_models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=350
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception as e:
            logger.error(f"Error calling model '{model}': {e}")
            continue

    return generate_fallback_response(history)

def generate_fallback_response(history):
    """
    Provides smart offline fallback responses for medical kiosk demo resilience.
    """
    user_messages = [m["content"].lower() for m in history if m["role"] == "user"]
    last_user_msg = user_messages[-1] if user_messages else ""

    if any(term in last_user_msg for term in ["fever", "temperature", "chill", "hot"]):
        return ("It sounds like you may be experiencing symptoms related to a fever or infection. "
                "Ensure you stay hydrated and rest. If your fever exceeds 102°F (38.9°C) or is accompanied "
                "by difficulty breathing, please seek medical evaluation promptly.")
    elif any(term in last_user_msg for term in ["headache", "migraine", "head pain"]):
        return ("Headaches can be caused by dehydration, stress, lack of sleep, or underlying strain. "
                "Try drinking water and resting in a quiet, dark room. If the pain is sudden and severe, "
                "or accompanied by vision changes, consult a physician immediately.")
    elif any(term in last_user_msg for term in ["cough", "chest", "throat", "cold"]):
        return ("Respiratory symptoms like coughing or throat discomfort are common with viral infections. "
                "Warm fluids and throat lozenges may help soothe discomfort. If you experience shortness of breath, "
                "chest tightness, or severe fatigue, seek immediate medical attention.")
    else:
        return ("Thank you for sharing your health details. Based on your inputs, please monitor your symptoms closely. "
                "If you feel unwell or your symptoms worsen, consult a licensed healthcare professional for a formal evaluation.")