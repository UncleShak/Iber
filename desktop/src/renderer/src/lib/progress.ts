export const BANDS = {
  starting: [0, 4, 1000], host: [4, 8, 1000], backup: [8, 28, 4000], patch: [28, 40, 2000],
  software: [40, 55, 2000], protection: [55, 80, 5000], recovery: [80, 90, 3000], engine: [90, 99, 2000],
} as const;

export function progressPct(phase: keyof typeof BANDS | "done", msInPhase: number): number {
  if (phase === "done") return 100;
  const [s, e, exp] = BANDS[phase];
  return Math.min(e - 1, s + (e - s) * (1 - Math.exp(-msInPhase / exp)));
}