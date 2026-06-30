from sqlalchemy import text
from rag.db import engine
from rag.embed import embed


def retrieve(question: str, patient_id: str, top_k: int = 4) -> list[dict]:
    """
    Find the most relevant chunks for a question using vector similarity search.
    """
    question_vector = embed(question)

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT
                content,
                source_type,
                metadata,
                1 - (embedding <=> CAST(:query_vec AS vector)) AS similarity
            FROM medical_chunks
            WHERE patient_id = :patient_id
            ORDER BY embedding <=> CAST(:query_vec AS vector)
            LIMIT :top_k
        """), {
            "query_vec"  : str(question_vector),
            "patient_id" : patient_id,
            "top_k"      : top_k
        }).fetchall()

    return [
        {
            "content"    : row[0],
            "source_type": row[1],
            "metadata"   : row[2],
            "similarity" : round(row[3], 3)
        }
        for row in rows
    ]