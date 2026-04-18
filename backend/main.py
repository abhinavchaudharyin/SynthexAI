# main.py
# SynthexAI ka main FastAPI server
# Sab files yahan connect hoti hain

import os
import asyncio
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv

# Apni files import karo
from guardrails import check_query
from rate_limiter import is_allowed
from search_handler import search_web
from llm_handler import call_all_llms
from synthesizer import synthesize
from voice_handler import transcribe_audio
from ocr_handler import extract_text_from_image

load_dotenv()

# FastAPI app banao
app = FastAPI(title="SynthexAI", version="1.0.0")

# CORS — frontend ko backend se baat karne do
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Request format
class QueryRequest(BaseModel):
    query: str
    user_id: str = "default_user"
    history: list = []


@app.get("/")
def home():
    return {"message": "SynthexAI is running!"}


@app.post("/chat")
async def chat(request: QueryRequest):
    """
    Main chat endpoint
    Text query receive karta hai aur answer deta hai
    """

    # Step 1 — Rate limit check
    limit = is_allowed(request.user_id)
    if not limit["allowed"]:
        return {"success": False, "answer": limit["reason"]}

    # Step 2 — Guardrails check
    guard = check_query(request.query)
    if not guard["allowed"]:
        return {"success": False, "answer": guard["reason"]}

    # Step 3 — Web search
    search_results = search_web(request.query)
    search_context = ""
    sources = []

    if search_results["success"]:
        search_context = search_results["quick_answer"]
        for r in search_results["results"]:
            search_context += f"\n{r['title']}: {r['content'][:200]}"
            sources.append({"title": r["title"], "url": r["url"]})

    # Step 4 — LLMs call karo
    llm_responses = await call_all_llms(
        query=request.query,
        search_context=search_context,
        history=request.history
    )

    # Step 5 — Synthesize
    final = await synthesize(request.query, llm_responses)

    return {
        "success": final["success"],
        "answer": final["answer"],
        "models_used": final["models_used"],
        "models_skipped": final["models_skipped"],
        "sources": sources
    }


@app.post("/voice-input")
async def voice_input(audio: UploadFile = File(...)):
    """
    Voice input endpoint
    Audio file receive karta hai, text return karta hai
    """
    audio_bytes = await audio.read()
    audio_file = ("audio.wav", audio_bytes, audio.content_type)
    result = transcribe_audio(audio_file)
    return result

@app.post("/ocr")
async def ocr(image: UploadFile = File(...)):
    """
    OCR endpoint
    Image receive karta hai, extracted text return karta hai
    """
    image_bytes = await image.read()
    mime_type = image.content_type or "image/jpeg"
    result = extract_text_from_image(image_bytes, mime_type)
    return result