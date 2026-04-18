import os
import asyncio
import logging
from dotenv import load_dotenv
from groq import AsyncGroq
from mistralai.async_client import MistralAsyncClient
from mistralai.models.chat_completion import ChatMessage
from tenacity import retry, stop_after_attempt, wait_exponential
from google import genai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize clients
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
mistral_client = MistralAsyncClient(api_key=os.getenv("MISTRAL_API_KEY"))

# Timeout configuration
TIMEOUT = 10

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_groq(messages: list) -> dict:
    """Call Groq's Llama 3 model"""
    try:
        logger.info("Calling Groq API...")
        response = await asyncio.wait_for(
            groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages
            ),
            timeout=TIMEOUT
        )
        return {
            "model": "Groq (Llama 3)",
            "success": True,
            "answer": response.choices[0].message.content
        }
    except asyncio.TimeoutError:
        logger.warning("Groq request timed out")
        return {"model": "Groq", "success": False, "answer": "", "reason": "Timeout"}
    except Exception as e:
        logger.error(f"Groq error: {str(e)}")
        return {"model": "Groq", "success": False, "answer": "", "reason": str(e)}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_gemini(messages: list) -> dict:
    try:
        logger.info("Calling Gemini API...")

        prompt_parts = [
            m["content"] for m in messages
            if m["role"] != "system"
        ]
        prompt = "\n".join(prompt_parts)

        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt
                )
            ),
            timeout=TIMEOUT
        )

        return {
            "model": "Gemini",
            "success": True,
            "answer": response.text
        }

    except asyncio.TimeoutError:
        return {"model": "Gemini", "success": False, "answer": "", "reason": "Timeout"}
    except Exception as e:
        return {"model": "Gemini", "success": False, "answer": "", "reason": str(e)}
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_mistral(messages: list) -> dict:
    """Call Mistral's model using async client"""
    try:
        logger.info("Calling Mistral API...")

        # Convert messages to Mistral's format
        mistral_messages = [
            ChatMessage(role=m["role"], content=m["content"])
            for m in messages
        ]

        # Use async client directly
        response = await asyncio.wait_for(
            mistral_client.chat(
                model="mistral-small-latest",
                messages=mistral_messages
            ),
            timeout=TIMEOUT
        )
        return {
            "model": "Mistral",
            "success": True,
            "answer": response.choices[0].message.content
        }
    except asyncio.TimeoutError:
        logger.warning("Mistral request timed out")
        return {"model": "Mistral", "success": False, "answer": "", "reason": "Timeout"}
    except Exception as e:
        logger.error(f"Mistral error: {str(e)}")
        return {"model": "Mistral", "success": False, "answer": "", "reason": str(e)}

async def call_all_llms(query: str, search_context: str = "", history: list = []) -> list:
    """
    Call all LLMs simultaneously with the given query
    """
    # Build system message
    system_msg = """You are SynthexAI — a powerful, intelligent assistant.
    Answer clearly, accurately and concisely.
    If search context is provided, use it for real time information."""

    if search_context:
        system_msg += f"\n\nReal-time web search results:\n{search_context}"

    # Prepare messages
    messages = [{"role": "system", "content": system_msg}]
    messages += history
    messages.append({"role": "user", "content": query})

    logger.info(f"Calling all models with query: {query[:50]}...")

    # Call all models concurrently
    results = await asyncio.gather(
        call_groq(messages),
        call_gemini(messages),
        call_mistral(messages),
        return_exceptions=False
    )

    return results
