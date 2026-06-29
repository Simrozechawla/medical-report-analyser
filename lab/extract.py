import os
import json
import fitz
from groq import Groq
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class LabResult(BaseModel):
    test_name     : str
    value         : float
    unit          : str
    reference_low : Optional[float] = None
    reference_high: Optional[float] = None
    flagged       : bool            = False

class LabReport(BaseModel):
    patient_name  : Optional[str] = None
    report_date   : Optional[str] = None
    results       : list[LabResult]


def extract_text_from_pdf(pdf_path: str) -> str:
    doc  = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def extract_lab_results(pdf_path: str) -> LabReport:
    raw_text = extract_text_from_pdf(pdf_path)

    prompt = f"""
You are a medical data extraction assistant.
Extract every lab test result from the text below.

Return ONLY a valid JSON object with this exact structure —
no explanation, no markdown, no backticks, just raw JSON:

{{
  "patient_name": "string or null",
  "report_date": "string or null",
  "results": [
    {{
      "test_name": "string",
      "value": number,
      "unit": "string",
      "reference_low": number or null,
      "reference_high": number or null,
      "flagged": true or false
    }}
  ]
}}

Rules:
- flagged = true if value is outside the reference range
- If no reference range is given, set flagged = false
- value must always be a number, never a string
- Do not include any text outside the JSON

Lab report text:
{raw_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw_json = response.choices[0].message.content.strip()

    if raw_json.startswith("```"):
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]
        raw_json = raw_json.strip()

    data   = json.loads(raw_json)
    report = LabReport(**data)
    return report