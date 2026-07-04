import os
from groq import Groq
from dotenv import load_dotenv
from rag.retrieve import retrieve

load_dotenv()



def answer_question(question: str, patient_id: str) -> dict:
    """
    Full RAG generation step:
      1. Retrieve relevant chunks (the "R")
      2. Build a prompt that forces the LLM to answer ONLY from those chunks
      3. Generate an answer with Groq (the "G")
      4. Return the answer + the sources used, so the answer is traceable
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    chunks = retrieve(question, patient_id=patient_id, top_k=4)

    if not chunks:
        return {
            "answer": "I don't have any medical data on file for this patient yet. Please upload an ECG or lab report first.",
            "sources": []
        }

    # Build context block from retrieved chunks
    context = "\n".join([f"- {c['content']}" for c in chunks])

    prompt = f"""You are a medical report assistant. Answer the patient's question using ONLY the information provided below. Do not add medical advice or information not present in the data. If the data doesn't fully answer the question, say so clearly.

Patient data:
{context}

Question: {question}

Answer concisely, in plain language a patient would understand."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "sources": [
            {"type": c["source_type"], "content": c["content"], "similarity": c["similarity"]}
            for c in chunks
        ]
    }