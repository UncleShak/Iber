// desktop/src/main/pipeline/runEngine.ts
import path from "node:path";
import { paths } from "../paths";
import { runProcess, type RunOut } from "./runProcess";

export function runEngine(
  runDir: string,
  runId: string,
  org: string,
  signal: AbortSignal
): Promise<RunOut> {
  const { cmd, prefixArgs, cwd } = paths.engine();
  return runProcess(
    cmd,
    [
      ...prefixArgs,
      "--in",
      path.join(runDir, "scan.json"),
      "--out",
      runDir,
      "--baseline",
      paths.baseline(),
      "--run-id",
      runId,
      "--org",
      org,
    ],
    { cwd, timeoutMs: 15_000, signal }
  );
}
