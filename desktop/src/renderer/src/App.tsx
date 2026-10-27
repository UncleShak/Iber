// desktop/src/renderer/src/App.tsx
// BRICK D ISOLATION TEST — REMOVE BEFORE FRANK MERGES BRICK C
// This file exercises the full IPC pipeline: license, scan, progress, results, file operations.
import { useEffect, useState } from "react";
import type { LicenseState, ScanProgress, ScanResult } from "../../shared/ipc";

const api = (window as any).antigravity;

export default function App() {
  const [lic, setLic] = useState<LicenseState | null>(null);
  const [token, setToken] = useState("");
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getLicense().then(setLic);
    const unsub = api.onProgress((p: ScanProgress) => setProgress(p));
    return () => unsub();
  }, []);

  const submit = async () => {
    const r = await api.submitLicense(token);
    setLic(r);
  };

  const scan = async () => {
    setScanning(true);
    setResult(null);
    setError(null);
    const r = await api.runScan();
    setScanning(false);
    if (r.ok) setResult(r);
    else setError(r.message);
  };

  const cancel = () => api.cancelScan();

  if (!lic) return <div style={{ padding: 32 }}>Loading…</div>;

  return (
    <div style={{ padding: 32, fontFamily: "Segoe UI, sans-serif", maxWidth: 800 }}>
      <h1>Antigravity — Brick D Isolation Test</h1>
      <p style={{ color: "#666", fontSize: 12 }}>
        ⚠️ This is a test renderer. Remove before Frank merges Brick C.
      </p>

      {lic.status === "valid" ? (
        <>
          <div style={{ padding: 16, background: "#ecfdf3", border: "1px solid #067647", borderRadius: 8, marginBottom: 16 }}>
            ✓ License valid: <b>{lic.lic}</b> ({lic.org})
          </div>

          {!scanning && !result && !error && (
            <button onClick={scan} style={{ padding: "12px 24px", fontSize: 16, background: "#067647", color: "white", border: "none", borderRadius: 6, cursor: "pointer" }}>
              Start scan
            </button>
          )}

          {scanning && (
            <div style={{ padding: 16, background: "#f2f4f7", borderRadius: 8 }}>
              <p>Scanning… phase: <b>{progress?.phase ?? "starting"}</b> ({progress?.elapsedMs ?? 0} ms)</p>
              <button onClick={cancel} style={{ padding: "8px 16px", background: "#b42318", color: "white", border: "none", borderRadius: 4, cursor: "pointer" }}>
                Cancel
              </button>
            </div>
          )}

          {error && (
            <div style={{ padding: 16, background: "#fef3f2", border: "1px solid #b42318", borderRadius: 8, color: "#b42318" }}>
              Error: {error}
            </div>
          )}

          {result && result.ok && (
            <div>
              <h2 style={{ color: "#067647" }}>✓ Scan complete</h2>
              <pre style={{ background: "#f2f4f7", padding: 16, borderRadius: 8, overflow: "auto", fontSize: 12 }}>
                {JSON.stringify(result.report, null, 2).slice(0, 3000)}
              </pre>
              <p>PDF available: {String(result.pdfAvailable)}</p>
              <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
                <button onClick={() => api.openPdf(result.runId)} style={{ padding: "8px 16px" }}>Open PDF</button>
                <button onClick={() => api.openHtml(result.runId)} style={{ padding: "8px 16px" }}>Open HTML</button>
                <button onClick={() => api.exportEvidence(result.runId)} style={{ padding: "8px 16px" }}>Export evidence</button>
                <button onClick={() => { setResult(null); setError(null); }} style={{ padding: "8px 16px" }}>Scan again</button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div>
          <p>License status: <b>{lic.status}</b></p>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste license token (e.g., dummy-token)"
              style={{ flex: 1, padding: 8, fontFamily: "monospace", border: "1px solid #ccc", borderRadius: 4 }}
            />
            <button onClick={submit} style={{ padding: "8px 16px", background: "#067647", color: "white", border: "none", borderRadius: 4, cursor: "pointer" }}>
              Activate
            </button>
          </div>
          <p style={{ fontSize: 12, color: "#666", marginTop: 8 }}>
            💡 Your data stays on this PC. Nothing is uploaded.
          </p>
        </div>
      )}
    </div>
  );
}
