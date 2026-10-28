// desktop/src/renderer/src/lib/progress.ts
// Progress model from manual §4.8: [bandStart %, bandEnd %, expected ms]
export const BANDS = {
  starting: [0, 4, 1000],
  host: [4, 8, 1000],
  backup: [8, 28, 4000],
  patch: [28, 40, 2000],
  software: [40, 55, 2000],
  protection: [55, 80, 5000],
  recovery: [80, 90, 3000],
  engine: [90, 99, 2000],
} as const;

export type BandPhase = keyof typeof BANDS;
export const PHASE_ORDER: BandPhase[] = [
  "starting", "host", "backup", "patch", "software", "protection", "recovery", "engine",
];

export const PHASE_MESSAGES: Record<BandPhase, string> = {
  starting: "Starting the check\u2026",
  host: "Looking at your Windows version\u2026",
  backup: "Looking for backups\u2026",
  patch: "Checking Windows updates\u2026",
  software: "Checking installed apps\u2026",
  protection: "Checking ransomware protection\u2026",
  recovery: "Checking recovery options\u2026",
  engine: "Building your report\u2026",
};

export function isBandPhase(p: string): p is BandPhase {
  return Object.prototype.hasOwnProperty.call(BANDS, p);
}

/** Approaches the end of the band but never reaches it until the next phase marker arrives. */
export function progressPct(phase: BandPhase | "done", msInPhase: number): number {
  if (phase === "done") return 100;
  const [s, e, exp] = BANDS[phase];
  return Math.min(e - 1, s + (e - s) * (1 - Math.exp(-Math.max(0, msInPhase) / exp)));
}