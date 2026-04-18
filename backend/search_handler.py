import os
from tavily import TavilyClient
from dotenv import load_dotenv

# .env file se API key load karo
load_dotenv()

# Tavily client banao
client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def search_web(query: str) -> dict:
    """
    Query ke liye web search karta hai
    Returns: search results with urls and content
    """
    
    try:
        # Tavily se search karo
        response = client.search(
            query=query,
            search_depth="basic",    # basic ya advanced
            max_results=5,           # top 5 results
            include_answer=True      # ek line ka quick answer bhi
        )
        
        # Results clean karke return karo
        return {
            "success": True,
            "quick_answer": response.get("answer", ""),
            "results": [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "content": r["content"]
                }
                for r in response.get("results", [])
            ]
        }
        
    except Exception as e:
        # Agar search fail ho jaaye
        return {
            "success": False,
            "quick_answer": "",
            "results": [],
            "error": str(e)
        }