import type { Category } from "../lib/reportSchema";

type Row = Category["evidence"][number];

// Status is always icon + colour (never colour alone). Plain Unicode symbols, no icon font needed.
const SYMBOL: Record<string, { ch: string; cls: string; label: string }> = {
  red: { ch: "\u25CF", cls: "text-rag-red", label: "Act now" },
  amber: { ch: "\u25B2", cls: "text-rag-amber", label: "Improve" },
  green: { ch: "\u2713", cls: "text-rag-green", label: "Good" },
  unavailable: { ch: "\u2298", cls: "text-rag-grey", label: "Not checked" },
  failed: { ch: "\u2715", cls: "text-rag-grey", label: "Check failed" },
};

const COULDNT_READ = "Couldn't read:";

function valueText(row: Row): string {
  // The engine may already include the prefix; don't double it.
  if (row.status === "failed" && !row.value.startsWith(COULDNT_READ)) return `${COULDNT_READ} ${row.value}`;
  return row.value;
}

export default function EvidenceTable({ evidence }: { evidence: Row[] }) {
  if (!evidence.length) return null;
  return (
    <table className="mt-3 w-full overflow-hidden rounded-md border text-sm">
      <tbody className="divide-y">
        {evidence.map((row, i) => {
          const muted = row.status === "unavailable" || row.status === "failed";
          const sym = row.status ? SYMBOL[row.status] : undefined;
          return (
            <tr key={i} className={muted ? "italic text-rag-grey" : "text-gray-700"}>
              <td className="w-1/3 bg-gray-50 px-3 py-2 font-medium">{row.label}</td>
              <td className="px-3 py-2">{valueText(row)}</td>
              <td className="w-8 px-3 py-2 text-center not-italic">
                {sym && (
                  <span className={sym.cls} role="img" aria-label={sym.label}>
                    {sym.ch}
                  </span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
