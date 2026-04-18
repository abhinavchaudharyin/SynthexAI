# SynthexAI 🤖

> Three Minds. One Answer.

A premium Multi-LLM orchestration system that simultaneously queries **Groq (Llama 3)**, **Google Gemini**, and **Mistral**, filters outlier responses, and synthesizes one perfect answer — with real-time web search, voice input, and OCR.

---
---

## Demo Video

[![SynthexAI Demo](https://img.shields.io/badge/Watch%20Demo-Google%20Drive-blue?style=for-the-badge&logo=google-drive)](https://drive.google.com/file/d/1CxSyKJYE84QsYdbPnmZ9W3nEXuejvZSc/view?usp=sharing)

> Click the badge above to watch the full demo video.

---

## Features

- **Multi-LLM Parallel Calls** — Groq, Gemini, Mistral simultaneously via asyncio
- **Real-time Web Search** — Tavily integration for live internet data
- **Outlier Filtering** — Detects and discards anomalous responses
- **Response Synthesis** — Lead model merges best answers into one
- **Voice Input** — Groq Whisper for speech-to-text
- **Image OCR** — Groq Vision extracts text from images
- **Guardrails** — Pre-filter for harmful queries
- **Confidence Score** — Shows agreement level across models
- **Source Display** — Real web sources shown with every answer
- **Premium UI** — Floating widget with expand/collapse

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, asyncio |
| LLM 1 | Groq — Llama 3 70B |
| LLM 2 | Google Gemini 1.5 Flash |
| LLM 3 | Mistral Small |
| Web Search | Tavily API |
| Voice Input | Groq Whisper Large V3 |
| OCR | Groq Vision (Llama 4 Scout) |
| Frontend | HTML, CSS, JavaScript |

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/abhinavchaudharyin/SynthexAI.git
cd SynthexAI
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add API Keys
Create a `.env` file in root:

    GROQ_API_KEY=your_key
    GEMINI_API_KEY=your_key
    MISTRAL_API_KEY=your_key
    TAVILY_API_KEY=your_key

    
### 4. Run backend
```bash
cd backend
uvicorn main:app --reload
```

### 5. Open frontend
Open `frontend/index.html` in browser

---

## Architecture

    User Query
        ↓
    Guardrails Check
        ↓
    Tavily Web Search
        ↓
    Parallel LLM Calls (Groq + Gemini + Mistral)
        ↓
    Outlier Filter
        ↓
    Synthesis (Lead Model)
        ↓
    Final Answer
---

## Author

**Abhinav Kumar Chaudhary**
- GitHub: [@abhinavchaudharyin](https://github.com/abhinavchaudharyin)
- LinkedIn: [abhinavchaudharyin](https://linkedin.com/in/abhinavchaudharyin)
