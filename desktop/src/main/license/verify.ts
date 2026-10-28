// desktop/src/main/license/verify.ts — offline Ed25519 licence check (manual §3.11)
import { createPublicKey, verify as edVerify, type KeyObject } from "node:crypto";
import publicPem from "../../../../shared/license/public-key.pem?raw";

export type LicenseReason = "malformed" | "unknown_key" | "bad_signature" | "not_yet_valid" | "expired" | "not_entitled";

export type LicenseResult =
  | { ok: true; lic: string; org: string; exp: number }
  | { ok: false; reason: "expired"; exp: number }
  | { ok: false; reason: Exclude<LicenseReason, "expired"> };

export const KEYS: Readonly<Record<string, KeyObject>> = Object.freeze({ "demo-2026": createPublicKey(publicPem) });
const SKEW = 24 * 3600;
const MAX_LEN = 4096;   // real tokens are ~400 chars; refuse huge input before decoding (LIC-01)
const B64U = /^[A-Za-z0-9_-]+$/;
const B64U_OR_EMPTY = /^[A-Za-z0-9_-]*$/;   // empty signature is well-formed but fails verification

const isStrArray = (a: unknown): a is string[] => Array.isArray(a) && a.every((x) => typeof x === "string");

export function verifyLicense(token: string, nowSec = Math.floor(Date.now() / 1000),
                              keys: Readonly<Record<string, KeyObject>> = KEYS): LicenseResult {
  if (typeof token !== "string" || token.length > MAX_LEN) return { ok: false, reason: "malformed" };
  const parts = token.trim().split(".");
  // Strict base64url: Node's decoder skips stray characters, which would let one licence have many spellings.
  if (parts.length !== 3 || parts[0] !== "AG1" || !B64U.test(parts[1]) || !B64U_OR_EMPTY.test(parts[2])) {
    return { ok: false, reason: "malformed" };
  }
  let p: any;
  try { p = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8")); } catch { return { ok: false, reason: "malformed" }; }
  if (p === null || typeof p !== "object" || Array.isArray(p)) return { ok: false, reason: "malformed" };
  if (p.v !== 1 || typeof p.kid !== "string" || typeof p.lic !== "string"
      || (p.org !== undefined && typeof p.org !== "string")
      || !Number.isFinite(p.exp) || !Number.isFinite(p.nbf) || !isStrArray(p.features)) return { ok: false, reason: "malformed" };
  if (!Object.prototype.hasOwnProperty.call(keys, p.kid)) return { ok: false, reason: "unknown_key" };
  let good = false;
  try { good = edVerify(null, Buffer.from(`AG1.${parts[1]}`, "ascii"), keys[p.kid], Buffer.from(parts[2], "base64url")); } catch { good = false; }
  if (!good) return { ok: false, reason: "bad_signature" };
  if (nowSec + SKEW < p.nbf) return { ok: false, reason: "not_yet_valid" };
  if (nowSec - SKEW > p.exp) return { ok: false, reason: "expired", exp: p.exp };
  if (!p.features.includes("scan")) return { ok: false, reason: "not_entitled" };
  return { ok: true, lic: p.lic, org: p.org ?? "", exp: p.exp };
}
