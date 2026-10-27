// desktop/src/main/runs.ts
// Manages run folders: validates runId, creates the folder, and cleans up older runs.
import fs from "node:fs/promises";
import path from "node:path";
import { paths } from "./paths";

const RUN_ID_REGEX = /^[0-9TZ:-]+_[0-9a-f]{4}$/;

export function validateRunId(runId: string): boolean {
  return RUN_ID_REGEX.test(runId);
}

export function generateRunId(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  const ts = `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}T${pad(d.getUTCHours())}-${pad(d.getUTCMinutes())}-${pad(d.getUTCSeconds())}Z`;
  const rand = Math.floor(Math.random() * 0x10000).toString(16).padStart(4, "0");
  return `${ts}_${rand}`;
}

export async function prepareRunFolder(runId: string): Promise<string> {
  if (!validateRunId(runId)) {
    throw new Error("Invalid runId format");
  }

  const runsRoot = paths.runsRoot();
  const runDir = path.join(runsRoot, runId);

  // Ensure the root runs directory exists
  await fs.mkdir(runsRoot, { recursive: true });

  // Clean up older run folders (keep only the latest, which is the current runId)
  try {
    const entries = await fs.readdir(runsRoot, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory() && entry.name !== runId && validateRunId(entry.name)) {
        try {
          await fs.rm(path.join(runsRoot, entry.name), { recursive: true, force: true });
        } catch {
          // Ignore delete failures as per manual §5.6 step 8
        }
      }
    }
  } catch {
    // Ignore readdir failures (e.g., if directory is temporarily locked)
  }

  // Create the current run folder
  await fs.mkdir(runDir, { recursive: true });
  return runDir;
}
