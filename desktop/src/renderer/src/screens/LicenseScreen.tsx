import { useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Alert } from "../components/ui/alert";
import type { ValidLicense } from "../../../shared/ipc";

// Messages from manual §3.11. unknown_key and bad_signature share one message on purpose.
const MESSAGES: Record<string, string> = {
  malformed: "That doesn't look like an Antigravity key. Check you copied all of it.",
  unknown_key: "This key isn't valid.",
  bad_signature: "This key isn't valid.",
  expired: "This key has expired. Ask us for a new one.",
  not_yet_valid: "This key isn't active yet. Check your PC's date and time.",
  not_entitled: "This key doesn't include scanning.",
};

export default function LicenseScreen({ onSuccess }: { onSuccess: (l: ValidLicense) => void }) {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (loading || !token.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await window.antigravity.submitLicense(token.trim());
      if (res.status === "valid") {
        onSuccess(res);
        return;
      }
      setError(res.status === "invalid" ? (MESSAGES[res.reason] ?? "This key isn't valid.") : "This key isn't valid.");
    } catch (e) {
      console.error(e);
      setError("Something went wrong checking the key. Please try again.");
    }
    setLoading(false);
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <h1 className="mb-2 text-2xl font-bold text-rag-grey">Antigravity Cyber Health Check</h1>
      <p className="mb-6 text-gray-500">A 1-minute, read-only check of this PC's ransomware readiness.</p>

      <div className="mb-4 flex w-full max-w-sm space-x-2">
        <Input
          placeholder="Enter License Key (AG1...)"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          className="font-mono text-black"
          autoFocus
        />
        <Button onClick={handleSubmit} disabled={loading || !token.trim()}>
          {loading ? "..." : "Activate"}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4 max-w-sm">
          {error}
        </Alert>
      )}

      <p className="mt-4 text-xs text-gray-400">Your data stays on this PC. Nothing is uploaded.</p>
    </div>
  );
}
