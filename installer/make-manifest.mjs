// installer/make-manifest.mjs — writes SHA-256 hashes of shipped resources (§5.8, §7.8)
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..");

function walk(dir, filterFn = () => true, baseDir = dir) {
  const results = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    const rel = path.relative(baseDir, full).replace(/\\/g, "/");
    if (entry.isDirectory()) {
      if (filterFn(rel, true)) {
        results.push(...walk(full, filterFn, baseDir));
      }
    } else if (entry.isFile()) {
      if (filterFn(rel, false)) {
        results.push({ full, rel });
      }
    }
  }
  return results;
}

function sha256(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

const files = {};

// 1. Collector (*.ps1 minus tests/, mocks/, docs/)
const collectorDir = path.join(repoRoot, "collector");
for (const { full, rel } of walk(collectorDir, (r, isDir) => {
  if (isDir) return !["tests", "mocks", "docs"].includes(r.split("/")[0]);
  return r.endsWith(".ps1") && !/^(tests|mocks|docs)\//.test(r);
})) {
  files[`collector/${rel}`] = sha256(full);
}

// 2. Engine (engine/dist/engine/**)
const engineDistDir = path.join(repoRoot, "engine", "dist", "engine");
try {
  if (statSync(engineDistDir).isDirectory()) {
    for (const { full, rel } of walk(engineDistDir)) {
      files[`engine/${rel}`] = sha256(full);
    }
  }
} catch {
  console.error("ERROR: engine/dist/engine not found. Build engine.exe first.");
  process.exit(1);
}

// 3. Baseline (baseline/software-baseline.json)
const baselineFile = path.join(repoRoot, "baseline", "software-baseline.json");
files["baseline/software-baseline.json"] = sha256(baselineFile);

const sorted = Object.fromEntries(
  Object.entries(files).sort(([a], [b]) => a.localeCompare(b))
);

const outPath = path.join(repoRoot, "desktop", "src", "main", "resource-hashes.json");
writeFileSync(outPath, JSON.stringify({ files: sorted }, null, 2) + "\n", "utf8");
console.log(`Wrote ${Object.keys(sorted).length} resource hashes to ${outPath}`);
