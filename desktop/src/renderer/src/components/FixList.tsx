import { ShieldAlert } from "lucide-react";

export default function FixList({ fixes }: { fixes: any[] }) {
  if (!fixes || fixes.length === 0) return null;

  return (
    <section className="bg-white p-6 rounded-lg border shadow-sm mb-8">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <ShieldAlert className="w-5 h-5 text-rag-red"/> Your top 3 fixes
      </h2>
      <div className="grid gap-4 md:grid-cols-3">
        {fixes.map((fix, i) => (
          <div key={fix.id} className="border p-4 rounded-md bg-gray-50">
            <h3 className="font-bold text-sm mb-2">{i + 1}. {fix.title}</h3>
            <p className="text-xs text-gray-600 mb-3">{fix.why}</p>
            <ul className="text-xs list-disc pl-4 space-y-1 text-gray-700">
              {fix.steps.map((s: string, j: number) => <li key={j}>{s}</li>)}
            </ul>
            <p className="text-xs text-gray-500 mt-4 italic">
              ~{fix.effort_minutes} min {fix.needs_admin && "· Needs Admin"}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}