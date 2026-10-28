// desktop/src/main/license/store.ts — read/write %APPDATA%\Antigravity\license.txt (manual §3.11, §5.6 steps 5-6)
// The caller passes the path (paths.licenseFile(), §5.5). Store only; verification is verify.ts's job.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";

export function readStoredToken(file: string): string | null {
  let text: string;
  try { text = readFileSync(file, "utf8"); } catch { return null; }
  const token = text.trim();
  return token === "" ? null : token;
}

export function saveToken(file: string, token: string): void {
  mkdirSync(path.dirname(file), { recursive: true });
  writeFileSync(file, token.trim(), "utf8");
}
