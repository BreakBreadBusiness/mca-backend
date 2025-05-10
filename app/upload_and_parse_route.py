
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PyPDF2 import PdfReader
from collections import defaultdict
from datetime import datetime
import io
import re

router = APIRouter()

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

            if "nsf" in lower_line:
                date_match = re.search(r"\d{2}/\d{2}/\d{4}", line)
                if date_match:
                    nsf_dates.add(date_match.group(0))

            dollar_matches = re.findall(r"\$[\d,]+\.\d{2}", line)
            date_match = re.search(r"\d{2}/\d{2}/\d{4}", line)

            if len(dollar_matches) >= 2 and date_match:
                balance_raw = dollar_matches[-1]
                balance = float(balance_raw.replace('$', '').replace(',', ''))
                date_str = date_match.group(0)
                if "-" in balance_raw or "(" in balance_raw:
                    negative_balance_days.add(date_str)
                daily_balances.append(balance)

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


@router.post("/upload-and-parse")
async def upload_and_parse(bank_statement: UploadFile = File(...)):
    try:
        if bank_statement.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
        contents = await bank_statement.read()
        result = parse_bank_statement_pdf(contents)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return JSONResponse(content={
            "filename": bank_statement.filename,
            "analysis": result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
