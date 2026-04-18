# voice_handler.py
# Voice Input — Groq Whisper (audio to text)
# Voice Output — removed

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Sirf Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(audio_file) -> dict:
    """
    Audio file ko text mein convert karta hai
    Groq Whisper use karta hai
    """
    try:
        transcription = groq_client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            language="en"
        )
        return {
            "success": True,
            "text": transcription.text
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": str(e)
        }