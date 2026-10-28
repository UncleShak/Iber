import { useEffect, useRef, useState } from "react";
import LicenseScreen from "./screens/LicenseScreen";
import ScanningScreen from "./screens/ScanningScreen";
import ResultsScreen from "./screens/ResultsScreen";
import ErrorScreen from "./screens/ErrorScreen";
import { Button } from "./components/ui/button";
import { reportSchema, type Report } from "./lib/reportSchema";
import type { ValidLicense } from "../../shared/ipc";

type AppState = "license" | "scanning" | "results" | "error";
type ScanOk = { report: Report; runId: string; pdfAvailable: boolean };

export default function App() {
  const [state, setState] = useState<AppState>("license");
  const [errorMessage, setErrorMessage] = useState("");
  const [license, setLicense] = useState<ValidLicense | null>(null);
  const [scan, setScan] = useState<ScanOk | null>(null);

  // Incremented on every scan start and on cancel, so a stale scan can never overwrite the screen.
  const runToken = useRef(0);

  useEffect(() => {
    window.antigravity
      .getLicense()
      .then((l) => {
        if (l.status === "valid") {
          setLicense(l);
          setState("results"); // results-empty state with a "Start scan" button (§4.9.1)
        }
      })
      .catch(() => {
        /* stay on the license screen */
      });
  }, []);

  const fail = (message: string) => {
    setErrorMessage(message);
    setState("error");
  };

  const triggerScan = async () => {
    const mine = ++runToken.current;
    setState("scanning");
    try {
      const res = await window.antigravity.runScan();
      if (mine !== runToken.current) return; // cancelled or superseded
      if (!res.ok) {
        fail(res.stage === "cancelled" ? "Scan cancelled." : res.message);
        return;
      }
      const parsed = reportSchema.safeParse(res.report);
      if (!parsed.success) {
        console.error(parsed.error);
        fail("The report couldn't be read.");
        return;
      }
      setScan({ report: parsed.data, runId: res.runId, pdfAvailable: res.pdfAvailable });
      setState("results");
    } catch (e) {
      console.error(e);
      if (mine === runToken.current) fail("Something went wrong while scanning. Please try again.");
    }
  };

  const cancelScan = () => {
    runToken.current++; // ignore whatever the running scan returns
    window.antigravity.cancelScan().catch(() => {});
    fail("Scan cancelled.");
  };

  return (
    <>
      {state === "license" && (
        <LicenseScreen
          onSuccess={(l) => {
            setLicense(l);
            triggerScan();
          }}
        />
      )}

      {state === "scanning" && <ScanningScreen onCancel={cancelScan} />}

      {state === "results" &&
        (scan ? (
          <ResultsScreen
            report={scan.report}
            runId={scan.runId}
            pdfAvailable={scan.pdfAvailable}
            license={license}
            onScanAgain={triggerScan}
          />
        ) : (
          <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-4 text-center">
            <h1 className="text-2xl font-bold text-rag-grey">Ready to check this PC</h1>
            <p className="max-w-md text-gray-500">
              A 1-minute, read-only check of this PC's ransomware readiness.
            </p>
            <Button onClick={triggerScan}>Start scan</Button>
          </div>
        ))}

      {state === "error" && (
        <ErrorScreen
          message={errorMessage}
          // A licensed user retries the scan; otherwise go back to licence entry.
          onTryAgain={() => (license ? triggerScan() : setState("license"))}
        />
      )}
    </>
  );
}
