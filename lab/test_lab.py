import os, sys, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from lab.extract import extract_lab_results

# We'll fake a PDF by writing a text file that looks like a lab report
SAMPLE_REPORT = """
PATHOLOGY REPORT
Patient: Simroze Chawla
Date: 2024-06-15

TEST NAME           RESULT    UNIT     REFERENCE RANGE
Hemoglobin          13.2      g/dL     12.0 - 15.5
White Blood Cells   11.8      10^3/uL  4.0 - 11.0   HIGH
Platelets           210       10^3/uL  150 - 400
Cholesterol         195       mg/dL    < 200
Blood Glucose       102       mg/dL    70 - 99       HIGH
Creatinine          0.9       mg/dL    0.6 - 1.2
"""

def make_sample_pdf(path):
    """Write the sample text into a real PDF using PyMuPDF."""
    import fitz
    doc  = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), SAMPLE_REPORT, fontsize=11)
    doc.save(path)
    doc.close()

if __name__ == "__main__":
    os.makedirs("data/samples", exist_ok=True)
    pdf_path = "data/samples/test_lab_report.pdf"
    make_sample_pdf(pdf_path)
    print(f"Sample PDF created → {pdf_path}")

    print("\nSending to Claude for extraction...\n")
    report = extract_lab_results(pdf_path)

    print(f"Patient : {report.patient_name}")
    print(f"Date    : {report.report_date}")
    print(f"\n{'TEST':<25} {'VALUE':>8} {'UNIT':<12} {'FLAGGED'}")
    print("-" * 55)
    for r in report.results:
        flag = "⚠ HIGH/LOW" if r.flagged else "✓"
        print(f"{r.test_name:<25} {r.value:>8} {r.unit:<12} {flag}")