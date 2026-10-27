// desktop/src/main/pipeline/runCollector.ts
// Spawns PowerShell 5.1 with the collector script. Uses the absolute path to
// powershell.exe to avoid PATH hijack and pwsh 7 (§3.12). Never uses
// -EncodedCommand or -WindowStyle Hidden (malware patterns).
import path from "node:path";
import { paths } from "../paths";
import { runProcess, type RunOut } from "./runProcess";

export function runCollector(
  runDir: string,
  runId: string,
  onLine: (line: string) => void,
  signal: AbortSignal
): Promise<RunOut> {
  const ps = path.join(
    process.env.SystemRoot ?? "C:\\Windows",
    "System32",
    "WindowsPowerShell",
    "v1.0",
    "powershell.exe"
  );

  return runProcess(
    ps,
    [
      "-NoLogo",
      "-NoProfile",
      "-NonInteractive",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      paths.collectorScript(),
      "-OutputPath",
      path.join(runDir, "scan.json"),
      "-RunId",
      runId,
    ],
    { cwd: runDir, timeoutMs: 45_000, onLine, signal }
  );
}
