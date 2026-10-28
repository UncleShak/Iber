import { Lock, ShieldAlert } from "lucide-react";
import type { Fix } from "../lib/reportSchema";

export default function FixList({ fixes }: { fixes: Fix[] }) {
  if (!fixes.length) return null;

  return (
    <section className="mb-8 rounded-lg border bg-white p-6 shadow-sm">
      <h2 className="mb-4 flex items-center gap-2 text-xl font-bold">
        <ShieldAlert className="h-5 w-5 text-rag-red" /> Your top 3 fixes
      </h2>
      <div className="grid gap-4 md:grid-cols-3">
        {fixes.slice(0, 3).map((fix, i) => (
          <div key={fix.id} className="rounded-md border bg-gray-50 p-4">
            <h3 className="mb-2 text-sm font-bold">
              {i + 1}. {fix.title}
            </h3>
            <p className="mb-3 text-xs text-gray-600">{fix.why}</p>
            <ul className="list-disc space-y-1 pl-4 text-xs text-gray-700">
              {fix.steps.map((s, j) => (
                <li key={j}>{s}</li>
              ))}
            </ul>
            <p className="mt-4 flex items-center gap-1 text-xs italic text-gray-500">
              {`~${fix.effort_minutes} min`}
              {fix.needs_admin && (
                <>
                  {" \u00b7 "}
                  <Lock className="h-3 w-3" aria-hidden="true" /> Needs admin
                </>
              )}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
