import { useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";
const PATIENT_ID = "simroze_test"; // hardcoded for now — single patient demo

function App() {
  const [ecgFile, setEcgFile] = useState(null);
  const [labFile, setLabFile] = useState(null);
  const [ecgResult, setEcgResult] = useState(null);
  const [labResult, setLabResult] = useState(null);
  const [uploading, setUploading] = useState(false);

  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);

  async function uploadEcg() {
    if (!ecgFile) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("patient_id", PATIENT_ID);
    formData.append("file", ecgFile);

    try {
      const res = await fetch(`${API_URL}/upload/ecg`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setEcgResult(data);
    } catch (err) {
      setEcgResult({ error: "Upload failed. Is the backend running?" });
    }
    setUploading(false);
  }

  async function uploadLab() {
    if (!labFile) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("patient_id", PATIENT_ID);
    formData.append("file", labFile);

    try {
      const res = await fetch(`${API_URL}/upload/lab`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setLabResult(data);
    } catch (err) {
      setLabResult({ error: "Upload failed. Is the backend running?" });
    }
    setUploading(false);
  }

  async function askQuestion() {
    if (!question.trim()) return;
    const userMsg = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion("");
    setAsking(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMsg.content, patient_id: PATIENT_ID }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error reaching the backend.", sources: [] },
      ]);
    }
    setAsking(false);
  }

  return (
    <div className="app">
      <h1>Medical Report Analyser</h1>

      <div className="panels">
        {/* Upload panel */}
        <div className="upload-panel">
          <h2>Upload Reports</h2>

          <div className="upload-box">
            <label>ECG Image</label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setEcgFile(e.target.files[0])}
            />
            <button onClick={uploadEcg} disabled={!ecgFile || uploading}>
              {uploading ? "Uploading..." : "Upload ECG"}
            </button>
            {ecgResult && (
              <div className="result-box">
                {ecgResult.error ? (
                  <p className="error">{ecgResult.error}</p>
                ) : (
                  <>
                    <p>Heart rate: {ecgResult.heart_rate_bpm} bpm</p>
                    <p>Beats detected: {ecgResult.beats_detected}</p>
                  </>
                )}
              </div>
            )}
          </div>

          <div className="upload-box">
            <label>Lab Report (PDF)</label>
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => setLabFile(e.target.files[0])}
            />
            <button onClick={uploadLab} disabled={!labFile || uploading}>
              {uploading ? "Uploading..." : "Upload Lab Report"}
            </button>
            {labResult && (
              <div className="result-box">
                {labResult.error ? (
                  <p className="error">{labResult.error}</p>
                ) : (
                  <>
                    <p>{labResult.results_count} results extracted</p>
                    <ul>
                      {labResult.results?.map((r, i) => (
                        <li key={i}>
                          {r.test_name}: {r.value} {r.unit}{" "}
                          {r.flagged ? "⚠️" : "✓"}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Chat panel */}
        <div className="chat-panel">
          <h2>Ask About Your Reports</h2>

          <div className="chat-messages">
            {messages.length === 0 && (
              <p className="placeholder">
                Upload a report above, then ask a question — e.g. "What is my
                heart rate?" or "Are any of my lab results abnormal?"
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`message ${m.role}`}>
                <p>{m.content}</p>
                {m.sources && m.sources.length > 0 && (
                  <details>
                    <summary>{m.sources.length} sources</summary>
                    <ul>
                      {m.sources.map((s, j) => (
                        <li key={j}>
                          [{s.type}] {s.content} (similarity: {s.similarity})
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
            ))}
            {asking && <p className="placeholder">Thinking...</p>}
          </div>

          <div className="chat-input">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && askQuestion()}
              placeholder="Ask a question..."
            />
            <button onClick={askQuestion} disabled={asking}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;