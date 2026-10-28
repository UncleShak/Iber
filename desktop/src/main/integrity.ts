// desktop/src/main/integrity.ts — packaged resource SHA-256 verification (§5.8, §7.8)
import { app } from "electron";
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

const TAMPER_MSG = "Some app files have been changed. Please reinstall Antigravity.";

const manifests = import.meta.glob("./resource-hashes.json", { eager: true }) as Record<
  string,
  { default?: { files?: Record<string, string> }; files?: Record<string, string> }
>;

function walkRel(dir: string, baseDir = dir): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    const rel = path.relative(baseDir, full).replace(/\\/g, "/");
    if (entry.isDirectory()) {
      out.push(...walkRel(full, baseDir));
    } else if (entry.isFile()) {
      out.push(rel);
    }
  }
  return out;
}

export function verifyPackagedResources():
  | { ok: true }
  | { ok: false; message: string; detail: string } {
  if (!app.isPackaged) return { ok: true };

  const mod = manifests["./resource-hashes.json"];
  const expected = mod?.default?.files ?? mod?.files;
  if (!expected || Object.keys(expected).length === 0) {
    return { ok: false, message: TAMPER_MSG, detail: "manifest missing" };
  }

  const resRoot = process.resourcesPath;

  // 1. Verify every expected file exists and matches its SHA-256
  for (const [rel, expectedHash] of Object.entries(expected)) {
    const full = path.join(resRoot, ...rel.split("/"));
    try {
      const actualHash = createHash("sha256").update(readFileSync(full)).digest("hex");
      if (actualHash !== expectedHash) {
        return { ok: false, message: TAMPER_MSG, detail: `hash mismatch: ${rel}` };
      }
    } catch {
      return { ok: false, message: TAMPER_MSG, detail: `missing resource: ${rel}` };
    }
  }

  // 2. Reject any extra files dropped into collector/, engine/, or baseline/ (TMP-04)
  for (const sub of ["collector", "engine", "baseline"]) {
    const subDir = path.join(resRoot, sub);
    try {
      if (statSync(subDir).isDirectory()) {
        for (const rel of walkRel(subDir, resRoot)) {
          if (!Object.prototype.hasOwnProperty.call(expected, rel)) {
            return { ok: false, message: TAMPER_MSG, detail: `unexpected resource: ${rel}` };
          }
        }
      }
    } catch {
      return { ok: false, message: TAMPER_MSG, detail: `missing resource directory: ${sub}` };
    }
  }

  return { ok: true };
}
