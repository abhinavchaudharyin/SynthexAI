import os
import base64
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Groq client banao
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Image se text extract karta hai
    image_bytes — image ka raw data
    mime_type — image/jpeg ya image/png
    """
    
    try:
        # Image ko base64 mein convert karo
        # Kyunki API ko base64 chahiye
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        
        # Groq Vision ko call karo
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """Please extract and return ALL text from this image.
                            If it's a document — return full text.
                            If it's a diagram — describe it and extract any text.
                            If it's a screenshot — return all visible text.
                            Return only the extracted content, nothing else."""
                        }
                    ]
                }
            ]
        )
        
        extracted_text = response.choices[0].message.content
        
        return {
            "success": True,
            "text": extracted_text
        }
        
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": str(e)
        }