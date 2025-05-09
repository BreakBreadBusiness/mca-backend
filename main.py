from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import openai
import os

# Create FastAPI app
app = FastAPI()

# Set OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

# ========= GPT ANALYSIS: APPLICATION ==========
def analyze_application(data: dict) -> str:
    prompt = f"""
You are an expert MCA underwriter.

Analyze the following application and determine:
1. Estimated MCA approval range
2. Risk level (low, medium, high)
3. Whether the $ requested is reasonable
4. Red flags or concerns
5. Key underwriting notes

Data:
{data}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Error: {str(e)}"


class ApplicationData(BaseModel):
    data: Any

@app.post("/analyze-app")
def analyze_app_endpoint(application: ApplicationData):
    result = analyze_application(application.data)
    return {"underwriting_summary": result}


# ========= GPT ANALYSIS: BANK PREVIEW ==========
def analyze_bank_preview(data: dict) -> str:
    prompt = f"""
You are a financial underwriter.

Review the following preview of a business bank statement and:
1. Estimate monthly revenue (if visible)
2. Assess consistency of cash flow
3. Point out red flags (NSFs, dips, etc.)
4. Estimate MCA funding range (or if unqualified)
5. Provide an underwriting summary for an MCA lender.

Data:
{data}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Error analyzing bank preview: {str(e)}"


class BankPreviewData(BaseModel):
    data: Any

@app.post("/analyze-bank")
def analyze_bank_endpoint(bank_data: BankPreviewData):
    result = analyze_bank_preview(bank_data.data)
    return {"bank_underwriting_summary": result}
