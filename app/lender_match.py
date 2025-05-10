from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from PyPDF2 import PdfReader
import io
import re
from collections import defaultdict
from datetime import datetime

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials are not set.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
router = APIRouter()

# ---------------- PDF PARSER ----------------
def parse_bank_statement_pdf(file_bytes: bytes):
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        lines = text.splitlines()
        income_keywords = [
            "sales", "credit", "deposit", "ach credit", "funds received",
            "zelle", "stripe", "square", "card payment", "payment received"
        ]

        monthly_totals = defaultdict(float)
        deposit_dates = set()
        nsf_dates = set()
        negative_balance_days = set()
        daily_balances = []

        for line in lines:
            lower_line = line.lower()

            # ---- Income detection ----
            if any(keyword in lower_line for keyword in income_keywords):
                amount_match = re.search(r"\$([\d,]+\.\d{2})", line)
                date_match = re.search(r"\d{2}/\d{2}/\d{4}", line)

                if amount_match and date_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    date_str = date_match.group(0)

                    try:
                        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                        month_key = date_obj.strftime("%Y-%m")
                        monthly_totals[month_key] += amount
                        deposit_dates.add(date_str)
                    except:
                        continue

            # ---- NSF detection ----
            if "nsf" in lower_line:
                date_match = re.search(r"\d{2}/\d{2}/\d{4}", line)
                if date_match:
                    nsf_dates.add(date_match.group(0))

            # ---- Balance detection: last dollar amount in line (likely ending balance) ----
            dollar_matches = re.findall(r"\$[\d,]+\.\d{2}", line)
            date_match = re.search(r"\d{2}/\d{2}/\d{4}", line)

            if len(dollar_matches) >= 2 and date_match:
                balance_raw = dollar_matches[-1]
                balance = float(balance_raw.replace('$', '').replace(',', ''))
                date_str = date_match.group(0)

                # Check if it's negative (none in your example, but supported)
                if "-" in balance_raw or "(" in balance_raw:
                    negative_balance_days.add(date_str)

                daily_balances.append(balance)

        # ---- Final calculations ----
        avg_monthly = (
            round(sum(monthly_totals.values()) / len(monthly_totals), 2)
            if monthly_totals else 0
        )

        avg_daily_balance = (
            round(sum(daily_balances) / len(daily_balances), 2)
            if daily_balances else 0
        )

        real_nsf_days = nsf_dates.intersection(negative_balance_days)

        return {
            "avgMonthlyRevenue": avg_monthly,
            "monthlyBreakdown": dict(monthly_totals),
            "avgDailyBalance": avg_daily_balance,
            "nsfDays": len(real_nsf_days),
            "negativeBalanceDays": len(negative_balance_days),
            "depositConsistency": len(deposit_dates),
            "recentFundingDetected": "funded by" in text.lower(),
            "existingMcaCount": text.lower().count("mca")
        }

    except Exception as e:
        print(f"Error in parsing: {e}")
        return {"error": str(e)}


# ---------------- MATCH LENDERS ROUTE ----------------
class LenderRequest(BaseModel):
    credit_score: int
    monthly_revenue: int
    avg_daily_balance: int
    time_in_business: int
    state: str
    industry: str
    has_existing_loans: Optional[bool] = False

@router.post("/match-lenders")
async def match_lenders(request: LenderRequest):
    try:
        query = supabase.table("lenders").select("*").execute()

        if "data" not in query or not query.data:
            raise HTTPException(status_code=404, detail="No lenders found in database.")

        matched = []

        for lender in query.data:
            if (
                lender["min_credit_score"] <= request.credit_score <= lender["max_credit_score"] and
                lender["min_monthly_revenue"] <= request.monthly_revenue <= lender["max_monthly_revenue"] and
                lender["min_daily_balance"] <= request.avg_daily_balance <= lender["max_daily_balance"] and
                lender["min_time_in_business"] <= request.time_in_business <= lender["max_time_in_business"] and
                request.state in lender["states"] and
                request.industry in lender["industries"] and
                (lender["accepts_existing_loans"] or not request.has_existing_loans)
            ):
                matched.append(lender)

        return {
            "matched_count": len(matched),
            "matched_lenders": matched
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching lenders: {str(e)}")

# ---------------- BANK STATEMENT UPLOAD ROUTE ----------------
@router.post("/upload-and-parse")
async def upload_and_parse(bank_statement: UploadFile = File(...)):
    try:
        if bank_statement.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

        contents = await bank_statement.read()
        result = parse_bank_statement_pdf(contents)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "filename": bank_statement.filename,
            "analysis": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
