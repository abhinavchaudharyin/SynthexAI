# main.py
import os
import asyncio
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
from pydantic import BaseModel
from dotenv import load_dotenv

from guardrails import check_query
from rate_limiter import is_allowed
from search_handler import search_web
from llm_handler import call_all_llms
from synthesizer import synthesize
from voice_handler import transcribe_audio
from ocr_handler import extract_text_from_image

load_dotenv()

app = FastAPI(title="SynthexAI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class QueryRequest(BaseModel):
    query: str
    user_id: str = "default_user"
    history: list = []


@app.get("/")
def home():
    return {"message": "SynthexAI is running!"}


@app.post("/chat")
async def chat(request: QueryRequest):
    limit = is_allowed(request.user_id)
    if not limit["allowed"]:
        return {"success": False, "answer": limit["reason"]}

    guard = check_query(request.query)
    if not guard["allowed"]:
        return {"success": False, "answer": guard["reason"]}

    search_results = search_web(request.query)
    search_context = ""
    sources = []
    if search_results["success"]:
        search_context = search_results["quick_answer"]
        for r in search_results["results"]:
            search_context += f"\n{r['title']}: {r['content'][:200]}"
            sources.append({"title": r["title"], "url": r["url"]})

    llm_responses = await call_all_llms(
        query=request.query,
        search_context=search_context,
        history=request.history
    )

    final = await synthesize(request.query, llm_responses)

    return {
        "success": final["success"],
        "answer": final["answer"],
        "models_used": final["models_used"],
        "models_skipped": final["models_skipped"],
        "sources": sources
    }


@app.post("/chat/stream")
async def chat_stream(request: QueryRequest):
    limit = is_allowed(request.user_id)
    if not limit["allowed"]:
        return {"success": False, "answer": limit["reason"]}

    guard = check_query(request.query)
    if not guard["allowed"]:
        return {"success": False, "answer": guard["reason"]}

    search_results = search_web(request.query)
    search_context = ""
    sources = []
    if search_results["success"]:
        search_context = search_results["quick_answer"]
        for r in search_results["results"]:
            search_context += f"\n{r['title']}: {r['content'][:200]}"
            sources.append({"title": r["title"], "url": r["url"]})

    llm_responses = await call_all_llms(
        query=request.query,
        search_context=search_context,
        history=request.history
    )

    final = await synthesize(request.query, llm_responses)

    async def stream_response():
        meta = {
            "type": "meta",
            "models_used": final["models_used"],
            "models_skipped": final["models_skipped"],
            "sources": sources
        }
        yield f"data: {json.dumps(meta)}\n\n"

        if final["success"] and final["answer"]:
            words = final["answer"].split(" ")
            for i, word in enumerate(words):
                chunk = {"type": "token", "text": word + (" " if i < len(words) - 1 else "")}
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.03)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.post("/voice-input")
async def voice_input(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    audio_file = ("audio.wav", audio_bytes, audio.content_type)
    result = transcribe_audio(audio_file)
    return result


@app.post("/ocr")
async def ocr(image: UploadFile = File(...)):
    image_bytes = await image.read()
    mime_type = image.content_type or "image/jpeg"
    result = extract_text_from_image(image_bytes, mime_type)
    return result