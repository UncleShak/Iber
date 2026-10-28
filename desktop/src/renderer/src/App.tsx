import { useState, useEffect } from "react";
import LicenseScreen from "./screens/LicenseScreen";
import ScanningScreen from "./screens/ScanningScreen";
import ResultsScreen from "./screens/ResultsScreen";
import ErrorScreen from "./screens/ErrorScreen";
import { reportSchema } from "./lib/reportSchema";

type AppState = "license" | "scanning" | "results" | "error";

export default function App() {
  const [currentState, setCurrentState] = useState<AppState>("license");
  const [errorMessage, setErrorMessage] = useState("");
  const [reportData, setReportData] = useState<any>(null);

  useEffect(() => {
    window.antigravity.getLicense().then((l: any) => {
      if (l.status === "valid") {
        setReportData(null);
        setCurrentState("results"); 
      }
    });
  }, []);

  const triggerScan = async () => {
    setCurrentState("scanning");
    const res = await window.antigravity.runScan();
    if (res.ok) {
      const parsed = reportSchema.safeParse(res.report);
      if (parsed.success) {
        setReportData(parsed.data);
        setCurrentState("results");
      } else {
        console.error(parsed.error);
        setErrorMessage("The report couldn't be read.");
        setCurrentState("error");
      }
    } else {
      setErrorMessage(res.message);
      setCurrentState("error");
    }
  };

  return (
    <>
      {currentState === "license" && <LicenseScreen onSuccess={triggerScan} />}
      {currentState === "scanning" && <ScanningScreen onCancel={() => { window.antigravity.cancelScan(); setErrorMessage("Scan cancelled."); setCurrentState("error"); }} />}
      {currentState === "results" && (reportData ? <ResultsScreen report={reportData} onScanAgain={triggerScan} /> : 
        <div className="flex items-center justify-center h-screen"><button onClick={triggerScan} className="bg-blue-600 text-white px-6 py-3 rounded shadow">Start Scan</button></div>
      )}
      {currentState === "error" && <ErrorScreen message={errorMessage} onTryAgain={() => setCurrentState("license")} />}
    </>
  );
}