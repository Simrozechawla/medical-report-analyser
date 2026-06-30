import json
from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from rag.db import engine, init_db

# This model runs fully locally — no API needed
# 384 dimensions, fast on CPU, good quality
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed(text_input: str) -> list[float]:
    """Convert a string into a 384-dim vector."""
    return model.encode(text_input).tolist()

def clear_patient_data(patient_id: str, source_type: str = None):
    """
    Remove existing chunks before re-inserting, so re-uploads don't duplicate data.
    If source_type is given, only clears that type (e.g. only 'ecg' chunks),
    so uploading a new lab report doesn't wipe out existing ECG data.
    """
    from sqlalchemy import text
    with engine.connect() as conn:
        if source_type:
            conn.execute(text("""
                DELETE FROM medical_chunks
                WHERE patient_id = :pid AND source_type = :stype
            """), {"pid": patient_id, "stype": source_type})
        else:
            conn.execute(text("""
                DELETE FROM medical_chunks WHERE patient_id = :pid
            """), {"pid": patient_id})
        conn.commit()

def store_ecg_findings(patient_id: str, heart_rate: float, beats: int):
    clear_patient_data(patient_id, source_type="ecg") 
    """
    Convert ECG analysis results into a text chunk and store it.
    We write findings as natural language so the embedding captures meaning.
    """
    content = (
        f"ECG analysis for patient {patient_id}: "
        f"Heart rate is {heart_rate} beats per minute. "
        f"{beats} heartbeats detected. "
        f"{'Heart rate is within normal range (60-100 bpm).' if 60 <= heart_rate <= 100 else 'Heart rate is outside normal range.'}"
    )

    _store_chunk(
        patient_id  = patient_id,
        source_type = "ecg",
        content     = content,
        metadata    = {"heart_rate": heart_rate, "beats_detected": beats}
    )
    print(f"Stored ECG findings for {patient_id}")


def store_lab_report(patient_id: str, report):
    clear_patient_data(patient_id, source_type="lab_report")
    """
    Store each lab result as a separate chunk so retrieval is precise.
    Storing them separately means "what is my cholesterol?" only retrieves
    the cholesterol chunk, not every single test result.
    """
    for result in report.results:
        status  = "abnormal (flagged)" if result.flagged else "normal"
        ref     = ""
        if result.reference_low is not None and result.reference_high is not None:
            ref = f"Reference range is {result.reference_low}–{result.reference_high} {result.unit}."

        content = (
            f"Lab result for patient {patient_id}: "
            f"{result.test_name} is {result.value} {result.unit}. "
            f"This is {status}. {ref}"
        )

        _store_chunk(
            patient_id  = patient_id,
            source_type = "lab_report",
            content     = content,
            metadata    = {
                "test_name"     : result.test_name,
                "value"         : result.value,
                "unit"          : result.unit,
                "flagged"       : result.flagged
            }
        )
    print(f"Stored {len(report.results)} lab results for {patient_id}")


def _store_chunk(patient_id, source_type, content, metadata):
    """Internal: embed a chunk and insert it into the database."""
    vector = embed(content)

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO medical_chunks
                (patient_id, source_type, content, embedding, metadata)
            VALUES
                (:patient_id, :source_type, :content, :embedding, :metadata)
        """), {
            "patient_id"  : patient_id,
            "source_type" : source_type,
            "content"     : content,
            "embedding"   : str(vector),
            "metadata"    : json.dumps(metadata)
        })
        conn.commit()