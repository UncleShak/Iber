// desktop/src/main/license/store.test.ts — license.txt read/write (manual §3.11, §5.6 steps 5-6)
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtempSync, rmSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { readStoredToken, saveToken } from "./store";

let dir: string;
beforeEach(() => { dir = mkdtempSync(path.join(tmpdir(), "ag-license-")); });
afterEach(() => { rmSync(dir, { recursive: true, force: true }); });

describe("license store", () => {
  it("returns null when no file exists", () => {
    expect(readStoredToken(path.join(dir, "license.txt"))).toBeNull();
  });
  it("returns null for an empty or whitespace-only file", () => {
    const f = path.join(dir, "license.txt");
    writeFileSync(f, " \r\n");
    expect(readStoredToken(f)).toBeNull();
  });
  it("round-trips a token", () => {
    const f = path.join(dir, "license.txt");
    saveToken(f, "AG1.abc.def");
    expect(readStoredToken(f)).toBe("AG1.abc.def");
  });
  it("trims whitespace on save and on read", () => {
    const f = path.join(dir, "license.txt");
    saveToken(f, "  AG1.abc.def\n");
    expect(readFileSync(f, "utf8")).toBe("AG1.abc.def");
    writeFileSync(f, "AG1.abc.def\r\n");
    expect(readStoredToken(f)).toBe("AG1.abc.def");
  });
  it("creates the parent folder if missing", () => {
    const f = path.join(dir, "Antigravity", "license.txt");
    saveToken(f, "AG1.abc.def");
    expect(existsSync(f)).toBe(true);
  });
  it("overwrites an existing token", () => {
    const f = path.join(dir, "license.txt");
    saveToken(f, "AG1.old.old");
    saveToken(f, "AG1.new.new");
    expect(readStoredToken(f)).toBe("AG1.new.new");
  });
});
