import { useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";
const PATIENT_ID = "simroze_test";

function EcgWave() {
  return (
    <div className="ecg-container">
      <svg className="ecg-svg" viewBox="0 0 840 56" preserveAspectRatio="none">
        <path
          className="ecg-path"
          d="M0,28 L60,28 L68,21 L76,21 L84,28 L100,28 L105,32 L111,2 L117,50 L122,28 L145,28 L152,17 L158,17 L165,28 L210,28 L270,28 L278,21 L286,21 L294,28 L310,28 L315,32 L321,2 L327,50 L332,28 L355,28 L362,17 L368,17 L375,28 L420,28 L480,28 L488,21 L496,21 L504,28 L520,28 L525,32 L531,2 L537,50 L542,28 L565,28 L572,17 L578,17 L585,28 L630,28 L690,28 L698,21 L706,21 L714,28 L730,28 L735,32 L741,2 L747,50 L752,28 L775,28 L782,17 L788,17 L795,28 L840,28"
          fill="none"
          stroke="#B8A898"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

function UploadCard({ label, accept, file, onFile, onUpload, uploading, result, icon }) {
  return (
    <div className={`upload-card ${result ? (result.error ? "has-error" : "has-success") : ""}`}>
      <div className="upload-card-header">
        <span className="upload-icon">{icon}</span>
        <span className="upload-label">{label}</span>
      </div>
      <label className="file-drop">
        <input type="file" accept={accept} onChange={(e) => onFile(e.target.files[0])} />
        {file ? (
          <span className="file-name">📄 {file.name}</span>
        ) : (
          <span className="file-placeholder">Choose file or drop here</span>
        )}
      </label>
      <button className="upload-btn" onClick={onUpload} disabled={!file || uploading}>
        {uploading ? "Analyzing…" : "Upload & Analyze"}
      </button>
      {result && (
        <div className={`upload-result ${result.error ? "error" : "success"}`}>
          {result.error ? (
            <p>⚠ {result.error}</p>
          ) : result.heart_rate_bpm ? (
            <>
              <p className="result-main">♥ {result.heart_rate_bpm} bpm</p>
              <p className="result-sub">{result.beats_detected} beats detected</p>
            </>
          ) : (
            <>
              <p className="result-main">✓ {result.results_count} results extracted</p>
              <div className="lab-results">
                {result.results?.map((r, i) => (
                  <div key={i} className={`lab-row ${r.flagged ? "flagged" : ""}`}>
                    <span>{r.test_name}</span>
                    <span>{r.value} {r.unit} {r.flagged ? "⚠" : "✓"}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function Message({ msg }) {
  const [showSources, setShowSources] = useState(false);
  return (
    <div className={`msg msg-${msg.role}`}>
      <p className="msg-content">{msg.content}</p>
      {msg.sources && msg.sources.length > 0 && (
        <div className="sources">
          <button className="sources-toggle" onClick={() => setShowSources(!showSources)}>
            {showSources ? "▾" : "▸"} {msg.sources.length} sources
          </button>
          {showSources && (
            <ul className="sources-list">
              {msg.sources.map((s, i) => (
                <li key={i}>
                  <span className={`source-tag ${s.type}`}>{s.type}</span>
                  {s.content}
                  <span className="sim">sim: {s.similarity}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [ecgFile, setEcgFile]     = useState(null);
  const [labFile, setLabFile]     = useState(null);
  const [ecgResult, setEcgResult] = useState(null);
  const [labResult, setLabResult] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [messages, setMessages]   = useState([]);
  const [question, setQuestion]   = useState("");
  const [asking, setAsking]       = useState(false);

  async function upload(endpoint, file) {
    setUploading(true);
    const form = new FormData();
    form.append("patient_id", PATIENT_ID);
    form.append("file", file);
    try {
      const res = await fetch(`${API_URL}/${endpoint}`, { method: "POST", body: form });
      return await res.json();
    } catch {
      return { error: "Upload failed. Is the backend running?" };
    } finally {
      setUploading(false);
    }
  }

  async function ask() {
    if (!question.trim()) return;
    const q = question;
    setMessages((m) => [...m, { role: "user", content: q }]);
    setQuestion("");
    setAsking(true);
    try {
      const res  = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, patient_id: PATIENT_ID }),
      });
      const data = await res.json();
      setMessages((m) => [...m, { role: "assistant", content: data.answer, sources: data.sources }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Error reaching the backend." }]);
    }
    setAsking(false);
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <div className="brand">
            <span className="brand-dot" />
            <span className="brand-name">MedAnalyser</span>
            <span className="brand-tag">AI Medical Report Analysis</span>
          </div>
          <div className="header-status">
            <span className="status-dot" />
            <span>Live</span>
          </div>
        </div>
        <EcgWave />
      </header>

      <main className="main">
        <aside className="panel left-panel">
          <h2 className="panel-title">Upload Reports</h2>
          <UploadCard
            label="ECG Image"
            accept="image/*"
            icon="〜"
            file={ecgFile}
            onFile={setEcgFile}
            onUpload={() => upload("upload/ecg", ecgFile).then(setEcgResult)}
            uploading={uploading}
            result={ecgResult}
          />
          <UploadCard
            label="Lab Report PDF"
            accept="application/pdf"
            icon="⊞"
            file={labFile}
            onFile={setLabFile}
            onUpload={() => upload("upload/lab", labFile).then(setLabResult)}
            uploading={uploading}
            result={labResult}
          />
        </aside>

        <section className="panel right-panel">
          <h2 className="panel-title">Ask About Your Results</h2>
          <div className="chat-body">
            {messages.length === 0 ? (
              <div className="chat-empty">
                <p>Upload a report on the left, then ask anything about your results.</p>
                <div className="suggestions">
                  {["What is my heart rate?", "Any abnormal results?", "Is my glucose normal?"].map((s) => (
                    <button key={s} className="suggestion" onClick={() => setQuestion(s)}>{s}</button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m, i) => <Message key={i} msg={m} />)
            )}
            {asking && <div className="msg msg-assistant typing">Analyzing your reports…</div>}
          </div>
          <div className="chat-input">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && ask()}
              placeholder="Ask about your results…"
            />
            <button onClick={ask} disabled={asking || !question.trim()}>Send</button>
          </div>
        </section>
      </main>
    </div>
  );
}