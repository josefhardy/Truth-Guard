from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

app = FastAPI()

# Define the expected input format
class ArticleRequest(BaseModel):
    url: HttpUrl  # Validates it's a proper URL

# Define the response for the POST request
@app.post("/api/detect-fake-news")
def detect_fake_news(request: ArticleRequest):
    # This is placeholder logic. Later, you'll:
    # - Scrape the article
    # - Analyze the content
    # - Return a real score

    return {
        "isReliable": True,
        "confidence": 85,
        "reasoning": [
            "This is a placeholder response.",
            "You’ll replace this with actual analysis."
        ],
        "sourceCredibility": 90,
        "factualAccuracy": 88,
        "biasScore": 25,
        "analysisDetails": {
            "domain": "example.com",
            "publishDate": "2024-01-15",
            "author": "John Smith",
            "wordCount": 1200
        }
    }

