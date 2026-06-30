import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/medical_rag")
engine = create_engine(DB_URL)

def init_db():
    """Create the pgvector extension and chunks table if they don't exist."""
    with engine.connect() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # One table stores everything — ECG findings and lab results
        # The embedding column is a 384-dimension vector
        # (all-MiniLM-L6-v2 produces 384-dim embeddings)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS medical_chunks (
                id          SERIAL PRIMARY KEY,
                patient_id  TEXT NOT NULL,
                source_type TEXT NOT NULL,   -- 'ecg' or 'lab_report'
                content     TEXT NOT NULL,   -- human-readable text of the finding
                embedding   vector(384),     -- the semantic vector
                metadata    JSONB,           -- extra info (heart rate, test name, etc.)
                created_at  TIMESTAMP DEFAULT NOW()
            )
        """))

        # Index for fast nearest-neighbor search
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS chunks_embedding_idx
            ON medical_chunks
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 10)
        """))

        conn.commit()
        print("Database initialized.")