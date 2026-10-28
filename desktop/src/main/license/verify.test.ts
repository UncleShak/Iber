// desktop/src/main/license/verify.test.ts — tamper cases for verifyLicense (manual §3.11, §7.4 LIC-01..05)
// Tokens are signed with a throwaway in-memory Ed25519 key; the real private key is never touched.
import { describe, it, expect } from "vitest";
import { generateKeyPairSync, sign, type KeyObject } from "node:crypto";
import { verifyLicense, KEYS } from "./verify";

const NOW = 1_800_000_000;
const DAY = 86_400;
const b64u = (b: Buffer | string) => Buffer.from(b).toString("base64url");

const test = generateKeyPairSync("ed25519");
const other = generateKeyPairSync("ed25519");
const keys: Record<string, KeyObject> = { "test-kid": test.publicKey };

function basePayload(over: Record<string, unknown> = {}) {
  return { v: 1, kid: "test-kid", lic: "AG-TEST-0001", org: "Test Org", tier: "demo",
           iat: NOW, nbf: NOW, exp: NOW + 60 * DAY, features: ["scan", "pdf"], ...over };
}

function issue(payload: unknown, key: KeyObject = test.privateKey): string {
  const head = "AG1." + b64u(JSON.stringify(payload));
  return head + "." + b64u(sign(null, Buffer.from(head, "ascii"), key));
}

const reason = (token: string, now = NOW, k = keys) => {
  const r = verifyLicense(token, now, k);
  return r.ok ? "ok" : r.reason;
};

describe("verifyLicense: valid token", () => {
  it("returns ok with lic, org and exp", () => {
    const p = basePayload();
    expect(verifyLicense(issue(p), NOW, keys)).toEqual({ ok: true, lic: "AG-TEST-0001", org: "Test Org", exp: p.exp });
  });
  it("trims surrounding whitespace and newlines", () => {
    expect(reason("  " + issue(basePayload()) + "\r\n")).toBe("ok");
  });
});

describe("verifyLicense: tampering (LIC-02, LIC-03, LIC-05)", () => {
  it("one character changed in the payload JSON (still valid JSON) -> bad_signature", () => {
    const [pre, pay, sig] = issue(basePayload()).split(".");
    const json = Buffer.from(pay, "base64url").toString("utf8").replace("Test Org", "Test Orh");
    expect(reason([pre, b64u(json), sig].join("."))).toBe("bad_signature");
  });
  it("payload segment re-spelled to decode to the same bytes -> bad_signature", () => {
    // Pad org so the JSON length leaves spare bits in the last base64 char, then find a twin char.
    let org = "Test Org";
    while (JSON.stringify(basePayload({ org })).length % 3 !== 1) org += " ";
    const [pre, pay, sig] = issue(basePayload({ org })).split(".");
    const bytes = Buffer.from(pay, "base64url");
    const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    const twin = [...alphabet].map((c) => pay.slice(0, -1) + c)
      .find((s) => s !== pay && Buffer.from(s, "base64url").equals(bytes));
    expect(twin).toBeDefined();
    expect(reason([pre, twin!, sig].join("."))).toBe("bad_signature");
  });
  it("payload re-encoded with a later exp -> bad_signature", () => {
    const [pre, , sig] = issue(basePayload()).split(".");
    const forged = b64u(JSON.stringify(basePayload({ exp: NOW + 3650 * DAY })));
    expect(reason([pre, forged, sig].join("."))).toBe("bad_signature");
  });
  it("signature swapped from another valid token -> bad_signature", () => {
    const t1 = issue(basePayload({ lic: "AG-TEST-0001" })).split(".");
    const t2 = issue(basePayload({ lic: "AG-TEST-0002" })).split(".");
    expect(reason([t1[0], t1[1], t2[2]].join("."))).toBe("bad_signature");
  });
  it("kid changed to one not in the key map -> unknown_key", () => {
    expect(reason(issue(basePayload({ kid: "evil-2099" })))).toBe("unknown_key");
  });
  it.each(["__proto__", "constructor", "toString", "hasOwnProperty"])("kid %s (inherited name) -> unknown_key", (kid) => {
    expect(reason(issue(basePayload({ kid })))).toBe("unknown_key");
  });
  it("non-base64url characters in either segment -> malformed (one licence, one spelling)", () => {
    const [pre, pay, sig] = issue(basePayload()).split(".");
    expect(reason([pre, pay, sig + "!!"].join("."))).toBe("malformed");
    expect(reason([pre, pay, "=" + sig].join("."))).toBe("malformed");
    expect(reason([pre, pay + "=", sig].join("."))).toBe("malformed");
    expect(reason([pre, pay.slice(0, 5) + " " + pay.slice(5), sig].join("."))).toBe("malformed");
  });
  it("signed by a different key -> bad_signature", () => {
    expect(reason(issue(basePayload(), other.privateKey))).toBe("bad_signature");
  });
  it("truncated or garbage signature -> bad_signature", () => {
    const [pre, pay] = issue(basePayload()).split(".");
    expect(reason([pre, pay, "AAAA"].join("."))).toBe("bad_signature");
    expect(reason([pre, pay, ""].join("."))).toBe("bad_signature");
  });
});

describe("verifyLicense: time window (24 h skew)", () => {
  it("expired beyond skew -> expired, with exp for the UI message", () => {
    const p = basePayload({ exp: NOW - 2 * DAY });
    expect(verifyLicense(issue(p), NOW, keys)).toEqual({ ok: false, reason: "expired", exp: p.exp });
  });
  it("expired but within 24 h skew -> ok", () => {
    expect(reason(issue(basePayload({ exp: NOW - DAY + 60 })))).toBe("ok");
  });
  it("nbf beyond skew in the future -> not_yet_valid", () => {
    expect(reason(issue(basePayload({ nbf: NOW + 2 * DAY })))).toBe("not_yet_valid");
  });
  it("nbf within 24 h skew -> ok", () => {
    expect(reason(issue(basePayload({ nbf: NOW + DAY - 60 })))).toBe("ok");
  });
});

describe("verifyLicense: entitlement", () => {
  it("features without scan -> not_entitled", () => {
    expect(reason(issue(basePayload({ features: ["pdf"] })))).toBe("not_entitled");
  });
});

describe("verifyLicense: malformed input (LIC-01)", () => {
  it.each([
    ["empty string", ""],
    ["whitespace only", "   "],
    ["hello", "hello"],
    ["AG1.", "AG1."],
    ["wrong prefix", "AG2.e30.AAAA"],
    ["four parts", "AG1.e30.AAAA.AAAA"],
    ["payload not JSON", "AG1." + b64u("not json") + ".AAAA"],
    ["payload JSON null", "AG1." + b64u("null") + ".AAAA"],
    ["payload JSON array", "AG1." + b64u("[1]") + ".AAAA"],
  ])("%s -> malformed", (_name, token) => {
    expect(reason(token)).toBe("malformed");
  });

  it.each([
    ["v missing", { v: undefined }],
    ["v = 2", { v: 2 }],
    ["kid not string", { kid: 7 }],
    ["lic missing", { lic: undefined }],
    ["org not string", { org: 7 }],
    ["exp not number", { exp: "soon" }],
    ["nbf missing", { nbf: undefined }],
    ["features not array", { features: "scan" }],
    ["features with non-string", { features: ["scan", 1] }],
  ])("signed payload with %s -> malformed", (_name, over) => {
    expect(reason(issue(basePayload(over)))).toBe("malformed");
  });

  it("5 000-character string -> malformed, quickly", () => {
    const t0 = Date.now();
    expect(reason("AG1." + "A".repeat(4996))).toBe("malformed");
    expect(reason("x".repeat(5000))).toBe("malformed");
    expect(Date.now() - t0).toBeLessThan(500);
  });

  it("non-string input -> malformed (IPC may pass anything)", () => {
    expect(reason(undefined as unknown as string)).toBe("malformed");
    expect(reason(42 as unknown as string)).toBe("malformed");
  });
});

describe("bundled key map", () => {
  it("contains demo-2026 as an Ed25519 public key", () => {
    expect(KEYS["demo-2026"].type).toBe("public");
    expect(KEYS["demo-2026"].asymmetricKeyType).toBe("ed25519");
  });
  it("is used by default: a forged demo-2026 token -> bad_signature", () => {
    const forged = issue(basePayload({ kid: "demo-2026" }), other.privateKey);
    const r = verifyLicense(forged, NOW);
    expect(r.ok ? "ok" : r.reason).toBe("bad_signature");
  });
});
