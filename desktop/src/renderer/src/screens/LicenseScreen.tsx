import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Alert } from "../components/ui/alert";

export default function LicenseScreen({ onSuccess }: { onSuccess: () => void }) {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true); setError("");
    const res = await window.antigravity.submitLicense(token);
    if (res.status === "valid") onSuccess();
    else {
      setError(res.reason === "malformed" ? "That doesn't look like an Antigravity key. Check you copied all of it." : "This key isn't valid.");
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <h1 className="text-2xl font-bold mb-2 text-rag-grey">Antigravity Cyber Health Check</h1>
      <p className="mb-6 text-gray-500">A 1-minute, read-only check of this PC's ransomware readiness.</p>
      
      <div className="w-full max-w-sm flex space-x-2 mb-4">
        <Input placeholder="Enter License Key (AG1...)" value={token} onChange={e => setToken(e.target.value)} className="font-mono text-black" />
        <Button onClick={handleSubmit} disabled={loading || !token}>{loading ? "..." : "Activate"}</Button>
      </div>
      {error && <Alert variant="destructive" className="max-w-sm mb-4">{error}</Alert>}
      <p className="text-xs text-gray-400 mt-4">Your data stays on this PC. Nothing is uploaded.</p>
    </div>
  );
}