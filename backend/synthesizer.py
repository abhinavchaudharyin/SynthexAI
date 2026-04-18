import os
import asyncio
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

# Lead model — Groq use karenge synthesis ke liye
lead_model = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

def detect_outlier(answers: list) -> list:
    """
    Bahut short ya bahut alag answers ko filter karta hai
    """
    
    # Sirf successful answers lo
    valid = [a for a in answers if a["success"]]
    
    if len(valid) <= 1:
        return valid
    
    # Har answer ki length nikalo
    lengths = [len(a["answer"]) for a in valid]
    avg_length = sum(lengths) / len(lengths)
    
    # Agar koi answer average se 70% kam ho — outlier hai
    filtered = [
        a for a in valid
        if len(a["answer"]) >= avg_length * 0.3
    ]
    
    return filtered


async def synthesize(query: str, answers: list) -> dict:
    """
    Valid answers ko Lead Model se synthesize karta hai
    """
    
    # Outlier filter karo
    valid_answers = detect_outlier(answers)
    
    # Agar koi valid answer nahi
    if not valid_answers:
        return {
            "success": False,
            "answer": "Sorry, all models failed to respond. Please try again.",
            "models_used": [],
            "models_skipped": []
        }
    
    # Konse models use hue, konse skip hue
    used = [a["model"] for a in valid_answers]
    skipped = [a["model"] for a in answers if not a["success"] or a["model"] not in used]
    
    # Agar sirf ek valid answer hai — directly return karo
    if len(valid_answers) == 1:
        return {
            "success": True,
            "answer": valid_answers[0]["answer"],
            "models_used": used,
            "models_skipped": skipped
        }
    
    # Multiple answers ko combine karo
    combined = ""
    for a in valid_answers:
        combined += f"\n\n{a['model']}:\n{a['answer']}"
    
    # Lead Model ko synthesis ke liye bhejo
    synthesis_prompt = f"""You are a synthesis expert.
You have received answers from multiple AI models for this query: "{query}"

Here are their responses:{combined}

Your task:
1. Read all answers carefully
2. Extract the best points from each
3. Remove any contradictions
4. Write ONE clear, accurate, complete final answer
5. Do not mention that you are combining answers

Write the final synthesized answer:"""

    try:
        response = await lead_model.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "user", "content": synthesis_prompt}
            ]
        )
        
        final_answer = response.choices[0].message.content
        
        return {
            "success": True,
            "answer": final_answer,
            "models_used": used,
            "models_skipped": skipped
        }
        
    except Exception as e:
        # Agar synthesis fail ho — pehla valid answer return karo
        return {
            "success": True,
            "answer": valid_answers[0]["answer"],
            "models_used": used,
            "models_skipped": skipped
        }