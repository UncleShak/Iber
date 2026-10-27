// desktop/src/main/pipeline/runProcess.ts
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";

export type RunOpts = {
  cwd: string;
  timeoutMs: number;
  onLine?: (line: string) => void;
  signal?: AbortSignal;
};

export type RunOut = {
  code: number | null;
  timedOut: boolean;
  cancelled: boolean;
  stderr: string;
};

export function runProcess(
  cmd: string,
  args: string[],
  opts: RunOpts
): Promise<RunOut> {
  return new Promise((resolve) => {
    const child = spawn(cmd, args, {
      cwd: opts.cwd,
      shell: false,
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stderr = "";
    let timedOut = false;
    let cancelled = false;

    const killTree = () => {
      if (child.pid) {
        spawn("taskkill", ["/pid", String(child.pid), "/T", "/F"], {
          windowsHide: true,
          shell: false,
        });
      }
    };

    const timer = setTimeout(() => {
      timedOut = true;
      killTree();
    }, opts.timeoutMs);

    opts.signal?.addEventListener("abort", () => {
      cancelled = true;
      killTree();
    });

    if (opts.onLine && child.stdout) {
      const rl = createInterface({ input: child.stdout });
      rl.on("line", (line) => opts.onLine!(line));
    }

    if (child.stderr) {
      child.stderr.on("data", (data: Buffer) => {
        const text = data.toString();
        if (stderr.length < 4000) {
          stderr += text.substring(0, 4000 - stderr.length);
        }
      });
    }

    child.on("close", (code) => {
      clearTimeout(timer);
      resolve({ code, timedOut, cancelled, stderr });
    });

    child.on("error", (err) => {
      clearTimeout(timer);
      resolve({ code: -1, timedOut, cancelled, stderr: String(err) });
    });
  });
}
