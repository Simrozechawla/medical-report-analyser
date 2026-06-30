import os
import sys
import shutil
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ecg.digitize import digitize
from lab.extract import extract_lab_results
from rag.embed import store_ecg_findings, store_lab_report
from rag.generate import answer_question
from rag.db import init_db

app = FastAPI(title="Medical Report Analyser API")

# Allow the React frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this to your actual frontend URL before deploying
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()


class ChatRequest(BaseModel):
    question: str
    patient_id: str


@app.post("/upload/ecg")
async def upload_ecg(patient_id: str = Form(...), file: UploadFile = File(...)):
    """Accepts an ECG image, digitizes it, stores findings."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        r_peaks, signal, hr = digitize(tmp_path)
        if hr is None:
            raise HTTPException(400, "Could not detect heartbeats in this image.")

        store_ecg_findings(patient_id=patient_id, heart_rate=hr, beats=len(r_peaks))

        return {
            "status": "success",
            "heart_rate_bpm": hr,
            "beats_detected": len(r_peaks)
        }
    finally:
        os.unlink(tmp_path)


@app.post("/upload/lab")
async def upload_lab(patient_id: str = Form(...), file: UploadFile = File(...)):
    """Accepts a lab report PDF, extracts results, stores them."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        report = extract_lab_results(tmp_path)
        store_lab_report(patient_id=patient_id, report=report)

        return {
            "status": "success",
            "results_count": len(report.results),
            "results": [r.dict() for r in report.results]
        }
    finally:
        os.unlink(tmp_path)


@app.post("/chat")
async def chat(request: ChatRequest):
    """Answer a question about a patient's medical data using RAG."""
    result = answer_question(request.question, patient_id=request.patient_id)
    return result


@app.get("/")
def root():
    return {"status": "Medical Report Analyser API is running"}