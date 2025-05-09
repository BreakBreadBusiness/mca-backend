from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
from openai import OpenAI
import os

# Initialize FastAPI app
app = FastAPI()

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use GPT-3.5 (low cost, free tier supported)
DEFAULT_MODEL = "gpt-3.5-turbo"

def get_gpt_response(prompt: str, model: str = DEFAULT_MODEL) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"


# ========== /analyze-app ==========

class ApplicationData(BaseModel):
    data: Any

@app.post("/analyze-app")
def analyze_app(application: ApplicationData):
    prompt = f"""
You are an expert MCA underwriter.

Analyze the following application and determine:
1. Estimated MCA approval range
2. Risk level (low, medium, high)
3. Whether the $ requested is reasonable
4. Red flags or concerns
5. Key underwriting notes

Data:
{application.data}
    """
    result = get_gpt_response(prompt)
    return {"underwriting_summary": result}


# ========== /analyze-bank ==========

class BankPreviewData(BaseModel):
    data: Any

@app.post("/analyze-bank")
def analyze_bank(bank_data: BankPreviewData):
    prompt = f"""
You are a financial underwriter.

Review the following preview of a business bank statement and:
1. Estimate monthly revenue (if visible)
2. Assess consistency of cash flow
3. Point out red flags (NSFs, dips, etc.)
4. Estimate MCA funding range (or if unqualified)
5. Provide an underwriting summary for an MCA lender.

Data:
{bank_data.data}
    """
    result = get_gpt_response(prompt)
    return {"bank_underwriting_summary": result}
