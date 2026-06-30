import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rag.db   import init_db
from rag.embed import store_ecg_findings, store_lab_report
from rag.retrieve import retrieve
from lab.extract  import extract_lab_results

if __name__ == "__main__":
    # 1. Initialize database
    print("Setting up database...")
    init_db()

    PATIENT = "simroze_test"

    # 2. Store fake ECG findings
    print("\nStoring ECG findings...")
    store_ecg_findings(patient_id=PATIENT, heart_rate=73.7, beats=6)

    # 3. Store lab report
    print("\nStoring lab report...")
    report = extract_lab_results("data/samples/test_lab_report.pdf")
    store_lab_report(patient_id=PATIENT, report=report)

    # 4. Test retrieval with different questions
    print("\n--- Testing retrieval ---\n")
    questions = [
        "What is my heart rate?",
        "Do I have any abnormal blood results?",
        "What is my cholesterol level?",
        "Is my blood glucose normal?"
    ]

    for q in questions:
        print(f"Q: {q}")
        chunks = retrieve(q, patient_id=PATIENT, top_k=2)
        for chunk in chunks:
            print(f"  [{chunk['source_type']} | similarity: {chunk['similarity']}]")
            print(f"  {chunk['content']}")
        print()