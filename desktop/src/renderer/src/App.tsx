import { useState } from "react";
import LicenseScreen from "./screens/LicenseScreen";
import ScanningScreen from "./screens/ScanningScreen";
import ResultsScreen from "./screens/ResultsScreen";
import ErrorScreen from "./screens/ErrorScreen";

type AppState = "license" | "scanning" | "results" | "error";

export default function App() {
  const [currentState, setCurrentState] = useState<AppState>("license");
  const [errorMessage, setErrorMessage] = useState<string>("");

  // Fired when the user clicks "Activate" on the License screen
  const handleLicenseSuccess = () => {
    setCurrentState("scanning");
    
    // Simulate a scan for 3 seconds since we don't have the backend yet!
    setTimeout(() => {
      setCurrentState("results");
    }, 3000);
  };

  // Allow users to cancel mid-scan
  const handleCancel = () => {
    setErrorMessage("Scan cancelled by user.");
    setCurrentState("error");
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {currentState === "license" && (
        <LicenseScreen onSuccess={handleLicenseSuccess} />
      )}
      
      {currentState === "scanning" && (
        <ScanningScreen onCancel={handleCancel} />
      )}
      
      {currentState === "results" && (
        <ResultsScreen report={{ overall: "Amber" }} onScanAgain={() => setCurrentState("scanning")} />
      )}
      
      {currentState === "error" && (
        <ErrorScreen message={errorMessage} onTryAgain={() => setCurrentState("license")} />
      )}
    </div>
  );
}