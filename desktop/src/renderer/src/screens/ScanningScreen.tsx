import { useEffect, useState, useRef } from "react";
import { Progress } from "../components/ui/progress";
import { Button } from "../components/ui/button";
import { progressPct, BANDS } from "../lib/progress";
import AdminHint from "../components/AdminHint";

export default function ScanningScreen({ onCancel }: { onCancel: () => void }) {
  const [phase, setPhase] = useState<keyof typeof BANDS>("starting");
  const [pct, setPct] = useState(0);
  const [isAdmin, setIsAdmin] = useState(true);
  const startTime = useRef(Date.now());

  useEffect(() => {
    window.antigravity.appInfo().then((info: any) => setIsAdmin(info.isAdmin));

    const unsub = window.antigravity.onProgress((p: any) => {
      setPhase(p.phase);
      startTime.current = Date.now();
    });
    
    const interval = setInterval(() => setPct(progressPct(phase, Date.now() - startTime.current)), 50);
    return () => { unsub(); clearInterval(interval); };
  }, [phase]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 max-w-lg mx-auto text-center">
      <h2 className="text-xl font-bold mb-6 text-rag-grey">Scanning...</h2>
      <Progress value={pct} className="h-3 mb-4 w-full" />
      <p className="mb-8 text-sm font-medium text-rag-grey uppercase tracking-wider">{phase}</p>
      <p className="mb-4 text-gray-500 text-sm">We only read settings. Nothing on your PC is changed.</p>
      
      {!isAdmin && <AdminHint />}
      
      <Button variant="ghost" onClick={onCancel} className="text-red-500">Cancel Scan</Button>
    </div>
  );
}