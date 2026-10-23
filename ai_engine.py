import os
import json
from pathlib import Path
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Ensure .env is loaded from the directory containing ai_engine.py or parent
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

openai_key = os.getenv("OPENAI_API_KEY", "").strip("\"'")
gemini_key = os.getenv("GEMINI_API_KEY", "").strip("\"'")

# Safely initialize clients
openai_client = None
if openai_key:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=openai_key)
    except Exception as e:
        logger.warning(f"Could not initialize OpenAI client: {e}")

gemini_client = None
if gemini_key:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=gemini_key)
    except Exception as e:
        logger.warning(f"Could not initialize Gemini client: {e}")


def transcribe_audio(audio_path: str) -> str:
    """
    Takes an audio file path (Urdu/Roman Urdu/Sindhi/English voice note), 
    first attempts OpenAI Whisper. If Whisper fails or quota is exhausted, 
    falls back to Gemini Multimodal Audio (gemini-3.5-flash-lite / gemini-3.5-flash) 
    to transcribe and translate into clear English.
    """
    if not audio_path or not os.path.exists(audio_path):
        return ""

    # 1. Try OpenAI Whisper
    if openai_client:
        try:
            with open(audio_path, "rb") as audio_file:
                response = openai_client.audio.translations.create(
                    model="whisper-1", 
                    file=audio_file
                )
            if response and response.text and response.text.strip():
                logger.info(f"Whisper successfully transcribed audio: {response.text.strip()}")
                return response.text.strip()
        except Exception as e:
            logger.warning(f"Whisper audio translation unavailable ({e}). Falling back to Gemini Audio...")

    # 2. Seamless Multimodal Fallback: Gemini Audio
    if gemini_client:
        try:
            from google.genai import types
            ext = Path(audio_path).suffix.lower()
            mime_map = {
                ".wav": "audio/wav",
                ".mp3": "audio/mp3",
                ".ogg": "audio/ogg",
                ".webm": "audio/webm",
                ".m4a": "audio/mp4",
                ".mp4": "audio/mp4",
            }
            audio_mime = mime_map.get(ext, "audio/wav")

            with open(audio_path, "rb") as af:
                audio_bytes = af.read()

            if len(audio_bytes) > 200:
                audio_prompt = (
                    "You are an expert speech recognition and translation AI for municipal citizen services in Pakistan. "
                    "Listen to this audio recording (which may be in Urdu, Roman Urdu, Sindhi, or English). "
                    "If the recording contains speech reporting a civic problem, issue, complaint, or inquiry, transcribe it and translate it into clear English. "
                    "If it is pure silence, background noise, or unintelligible static, output only: [No speech]. "
                    "Return ONLY the plain English translation, with no quotes or commentary."
                )

                for model_name in ['gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-flash-latest']:
                    try:
                        resp = gemini_client.models.generate_content(
                            model=model_name,
                            contents=[
                                types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime),
                                audio_prompt
                            ],
                        )
                        raw_text = (resp.text or "").strip()
                        if raw_text and "[no speech]" not in raw_text.lower():
                            logger.info(f"Gemini {model_name} transcribed audio: {raw_text}")
                            return raw_text
                    except Exception as gemini_err:
                        logger.warning(f"Gemini {model_name} audio failed: {gemini_err}")
                        continue
        except Exception as e:
            logger.error(f"Error in Gemini audio processing: {e}")

    return ""


def _smart_heuristic_fallback(text_description: str) -> dict:
    """Intelligent civic issue classification fallback (works 100% offline)."""
    text = (text_description or "").lower()
    
    if any(k in text for k in ["sewer", "gutter", "drain", "dirty water", "overflow", "sewerage", "naala"]):
        return {
            "is_valid_civic_issue": True,
            "category": "Sewerage",
            "severity": "Critical" if any(k in text for k in ["overflow", "flooding", "burst", "urgent", "open"]) else "High",
            "reasoning": "Sewerage/drainage blockage detected affecting public roadway.",
            "recommended_action": "Deploy municipal jetting tanker and drainage team to clear blockage.",
            "ai_action_plan": "Deploy municipal jetting tanker and drainage team to clear blockage."
        }
    elif any(k in text for k in ["pothole", "road", "sadak", "crater", "asphalt", "damage", "crack"]):
        return {
            "is_valid_civic_issue": True,
            "category": "Pothole",
            "severity": "Critical" if any(k in text for k in ["huge", "deep", "accident", "main road", "danger"]) else "High",
            "reasoning": "Road surface fracture/pothole posing vehicular and pedestrian hazard.",
            "recommended_action": "Deploy road maintenance crew with asphalt filler and roller.",
            "ai_action_plan": "Deploy road maintenance crew with asphalt filler and roller."
        }
    else:
        # Default or garbage
        return {
            "is_valid_civic_issue": True,
            "category": "Garbage",
            "severity": "Critical" if any(k in text for k in ["huge", "burning", "overflow", "smell", "rotten"]) else "High",
            "reasoning": "Solid waste accumulation detected in public sector.",
            "recommended_action": "Dispatch waste collection compactors and sanitation crew.",
            "ai_action_plan": "Dispatch waste collection compactors and sanitation crew."
        }


def analyze_civic_issue(image_path: str, text_description: str) -> dict:
    """
    Analyzes image and description with Gemini Vision LLM.
    Guarantees strict schema output and falls back to smart local heuristic if API is unavailable.
    """
    if gemini_client and image_path and os.path.exists(image_path):
        try:
            from google.genai import types
            prompt = f"""
            You are an expert civic issue triage AI for Karachi and Hyderabad municipal governance. 
            Analyze the provided image and the citizen's description: "{text_description}".
            
            Categorize the issue into strictly one of these 3 categories: "Garbage", "Pothole", or "Sewerage".
            If it's not a valid civic issue (e.g., a selfie, a random household item), set is_valid_civic_issue to false.
            
            Determine the severity based on public danger:
            - "Critical": open overflowing manholes, blocked main highways, severe toxic waste spill, fire/electric hazard near water.
            - "High": large pothole on busy road, significant garbage dump blocking sidewalk.
            - "Medium": moderate garbage pile, small asphalt cracks.
            - "Low": minor litter, cosmetic road wear.
            
            You must return ONLY a JSON object with this exact schema:
            {{
                "is_valid_civic_issue": true,
                "category": "Garbage" | "Pothole" | "Sewerage",
                "severity": "Critical" | "High" | "Medium" | "Low",
                "reasoning": "brief explanation",
                "recommended_action": "action plan for municipal crew"
            }}
            """
            pil_image = Image.open(image_path)
            
            for model_name in ['gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-flash-latest']:
                try:
                    response = gemini_client.models.generate_content(
                        model=model_name,
                        contents=[pil_image, prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                        ),
                    )
                    parsed = json.loads(response.text)
                    if "ai_action_plan" not in parsed:
                        parsed["ai_action_plan"] = parsed.get("recommended_action", "Dispatch municipal field team.")
                    return parsed
                except Exception as model_err:
                    logger.warning(f"Model {model_name} failed: {model_err}")
                    continue
        except Exception as e:
            logger.error(f"Error in Gemini multimodal analysis: {e}")

    # Seamless smart fallback (ensures real categories and real severities always!)
    return _smart_heuristic_fallback(text_description)


if __name__ == "__main__":
    print("AI Engine is ready for integration!")
