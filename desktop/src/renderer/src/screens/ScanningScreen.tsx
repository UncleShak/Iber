import { useEffect, useRef, useState } from "react";
import { Progress } from "../components/ui/progress";
import { Button } from "../components/ui/button";
import AdminHint from "../components/AdminHint";
import { PHASE_MESSAGES, isBandPhase, progressPct, type BandPhase } from "../lib/progress";

export default function ScanningScreen({ onCancel }: { onCancel: () => void }) {
  const [phase, setPhase] = useState<BandPhase | "done">("starting");
  const [pct, setPct] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [isAdmin, setIsAdmin] = useState(true);

  const phaseRef = useRef<BandPhase | "done">("starting");
  const phaseStart = useRef(performance.now());
  const scanStart = useRef(performance.now());
  const maxPct = useRef(0); // the bar never moves backwards

  useEffect(() => {
    window.antigravity
      .appInfo()
      .then((i) => setIsAdmin(i.isAdmin))
      .catch(() => {});

    // One subscription for the whole screen lifetime, so no progress events are missed.
    const unsub = window.antigravity.onProgress((p) => {
      if (p.phase !== "done" && !isBandPhase(p.phase)) return; // ignore unknown phases
      phaseRef.current = p.phase;
      phaseStart.current = performance.now();
      setPhase(p.phase);
    });

    let raf = 0;
    const tick = () => {
      const now = performance.now();
      maxPct.current = Math.max(maxPct.current, progressPct(phaseRef.current, now - phaseStart.current));
      setPct(maxPct.current);
      setElapsed(Math.floor((now - scanStart.current) / 1000));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    return () => {
      unsub();
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center p-8 text-center">
      <h2 className="mb-6 text-xl font-bold text-rag-grey">Scanning...</h2>
      <Progress value={pct} className="mb-4 h-3 w-full" />
      <p className="mb-1 text-sm font-medium text-rag-grey">
        {phase === "done" ? "Finishing up\u2026" : PHASE_MESSAGES[phase]}
      </p>
      <p className="mb-8 text-xs text-gray-400">{elapsed}s</p>
      <p className="mb-4 text-sm text-gray-500">We only read settings. Nothing on your PC is changed.</p>

      {!isAdmin && <AdminHint />}

      <Button variant="ghost" onClick={onCancel} className="text-rag-red">
        Cancel
      </Button>
    </div>
  );
}
