// desktop/src/main/paths.ts
// One resolver for every on-disk dependency. Packaged paths come from
// process.resourcesPath; __dirname would point inside app.asar (§5.5).
import { app } from "electron";
import path from "node:path";

// Dev app.getAppPath() is <repo>\desktop, so the repo is its parent.
const repoRoot = () => path.resolve(app.getAppPath(), "..");
const res = (...p: string[]) => path.join(process.resourcesPath, ...p);
const powershell = () => path.join(
  process.env.SystemRoot ?? "C:\\Windows",
  "System32", "WindowsPowerShell", "v1.0", "powershell.exe"
);

export const paths = {
  collectorScript: () => {
    if (app.isPackaged) return res("collector", "collector.ps1");
    // Dev-only isolation seam: no Brick B checkout needed.
    if (process.env.AG_STUB === "1") {
      return path.join(repoRoot(), "installer", "stubs", "collector-stub.ps1");
    }
    return path.join(repoRoot(), "collector", "collector.ps1");
  },

  baseline: () => app.isPackaged
    ? res("baseline", "software-baseline.json")
    : path.join(repoRoot(), "baseline", "software-baseline.json"),

  engine: () => {
    if (app.isPackaged) {
      const dir = res("engine");
      return { cmd: path.join(dir, "engine.exe"), prefixArgs: [] as string[], cwd: dir };
    }
    if (process.env.AG_STUB === "1") {
      const dir = path.join(repoRoot(), "installer", "stubs");
      return {
        cmd: powershell(),
        prefixArgs: [
          "-NoLogo", "-NoProfile", "-NonInteractive",
          "-ExecutionPolicy", "Bypass", "-File",
          path.join(dir, "engine-stub.ps1"),
        ],
        cwd: dir,
      };
    }
    if (process.env.AG_ENGINE_EXE === "1") {
      const dir = path.join(repoRoot(), "engine", "dist", "engine");
      return { cmd: path.join(dir, "engine.exe"), prefixArgs: [] as string[], cwd: dir };
    }
    const dir = path.join(repoRoot(), "engine");
    return {
      cmd: path.join(dir, ".venv", "Scripts", "python.exe"),
      prefixArgs: ["-m", "antigravity_engine"],
      cwd: dir,
    };
  },

  runsRoot: () => path.join(
    process.env.LOCALAPPDATA ?? app.getPath("userData"), "Antigravity", "runs"),
  logsRoot: () => path.join(
    process.env.LOCALAPPDATA ?? app.getPath("userData"), "Antigravity", "logs"),
  licenseFile: () => path.join(app.getPath("userData"), "license.txt"),

  // Stubs and mock mode must be structurally impossible in a shipped build.
  mockEnabled: () => !app.isPackaged && process.env.AG_MOCK === "1",
};
