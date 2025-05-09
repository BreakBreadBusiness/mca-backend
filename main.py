from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import google.generativeai as genai
import os

# Set up Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create the Gemini model
model = genai.GenerativeModel("gemini-1.5-pro")

# Initialize FastAPI app
app = FastAPI()

# Underwriting helper
def get_underwriting_response(prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Input schemas
class ApplicationData(BaseModel):
    data: Any

class BankPreviewData(BaseModel):
    data: Any

# Endpoint: Analyze Application
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
    result = get_underwriting_response(prompt)
    return {"underwriting_summary": result}

# Endpoint: Analyze Bank Statement Preview
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
    result = get_underwriting_response(prompt)
    return {"bank_underwriting_summary": result}
