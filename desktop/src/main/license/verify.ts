// desktop/src/main/license/verify.ts
// PLACEHOLDER copied from manual section 3.11 by Brick D so main compiles.
// Owner: Shakir (Brick B). Replace this file freely; keep the exported
// verifyLicense / LicenseResult signatures that main/ipc.ts uses.
// Only deviation from 3.11: the key map is built on first use and skips an
// empty public-key.pem, so the app does not crash before keygen has run.
import { createPublicKey, verify as edVerify, type KeyObject } from "node:crypto";
import publicPem from "../../../../shared/license/public-key.pem?raw";

export type LicenseResult =
  | { ok: true; lic: string; org: string; exp: number }
  | { ok: false; reason: "malformed" | "unknown_key" | "bad_signature" | "not_yet_valid" | "expired" | "not_entitled" };

let keys: Record<string, KeyObject> | null = null;
const getKeys = () => {
  if (!keys) {
    keys = {};
    if (publicPem.trim()) keys["demo-2026"] = createPublicKey(publicPem);
  }
  return keys;
};
const SKEW = 24 * 3600;

export function verifyLicense(token: string, nowSec = Math.floor(Date.now() / 1000)): LicenseResult {
  const parts = token.trim().split(".");
  if (parts.length !== 3 || parts[0] !== "AG1") return { ok: false, reason: "malformed" };
  let p: any;
  try { p = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8")); } catch { return { ok: false, reason: "malformed" }; }
  if (p?.v !== 1 || typeof p.kid !== "string" || typeof p.exp !== "number" || typeof p.nbf !== "number"
      || typeof p.lic !== "string" || !Array.isArray(p.features)) return { ok: false, reason: "malformed" };
  const key = getKeys()[p.kid];
  if (!key) return { ok: false, reason: "unknown_key" };
  const good = edVerify(null, Buffer.from(`AG1.${parts[1]}`, "ascii"), key, Buffer.from(parts[2], "base64url"));
  if (!good) return { ok: false, reason: "bad_signature" };
  if (nowSec + SKEW < p.nbf) return { ok: false, reason: "not_yet_valid" };
  if (nowSec - SKEW > p.exp) return { ok: false, reason: "expired" };
  if (!p.features.includes("scan")) return { ok: false, reason: "not_entitled" };
  return { ok: true, lic: p.lic, org: String(p.org ?? ""), exp: p.exp };
}
