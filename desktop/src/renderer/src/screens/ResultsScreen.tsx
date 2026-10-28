import { useState } from "react";
import { Button } from "../components/ui/button";
import { Separator } from "../components/ui/separator";
import StatusBadge from "../components/StatusBadge";
import CategoryCard from "../components/CategoryCard";
import FixList from "../components/FixList";
import { Download, FileText } from "lucide-react";
import type { Fix, Report } from "../lib/reportSchema";
import type { ValidLicense } from "../../../shared/ipc";

type Props = {
  report: Report;
  runId: string;
  pdfAvailable: boolean;
  license: ValidLicense | null;
  onScanAgain: () => void;
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString("en-ZA", { dateStyle: "medium", timeStyle: "short" });
}

export default function ResultsScreen({ report, runId, pdfAvailable, license, onScanAgain }: Props) {
  const [note, setNote] = useState("");

  const topFixes = report.top_fixes
    .map((id) => report.fixes.find((f) => f.id === id))
    .filter((f): f is Fix => f !== undefined);

  const run = async (action: () => Promise<{ ok: boolean }>, failMessage: string) => {
    setNote("");
    try {
      const r = await action();
      if (!r.ok) setNote(failMessage);
    } catch (e) {
      console.error(e);
      setNote(failMessage);
    }
  };

  return (
    <div className="min-h-screen bg-rag-grey-bg p-8 pb-24 text-rag-grey">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="mb-8 flex items-start justify-between gap-4">
          <div>
            <h1 className="mb-2 text-3xl font-bold text-black">Scan Results</h1>
            <p className="text-lg text-gray-700">{report.summary}</p>
            <p className="mt-1 text-sm text-gray-500">Checked on {formatDate(report.generated_at)}</p>
          </div>
          <StatusBadge status={report.overall} />
        </header>

        <FixList fixes={topFixes} />

        <Separator className="my-8" />

        <section>
          {report.categories.map((c) => (
            <CategoryCard key={c.id} category={c} />
          ))}
        </section>

        <div className="mt-8 flex flex-wrap gap-4">
          <Button
            disabled={!pdfAvailable}
            onClick={() => run(() => window.antigravity.openPdf(runId), "Couldn't open the PDF.")}
          >
            <FileText className="mr-2 h-4 w-4" /> Open one-page action plan (PDF)
          </Button>
          <Button
            variant="outline"
            onClick={() => run(() => window.antigravity.openHtml(runId), "Couldn't open the full report.")}
          >
            Open full report
          </Button>
          <Button
            variant="secondary"
            onClick={() => run(() => window.antigravity.exportEvidence(runId), "Nothing was saved.")}
          >
            <Download className="mr-2 h-4 w-4" /> Export evidence for insurer
          </Button>
          <div className="flex-1" />
          <Button variant="ghost" onClick={onScanAgain}>
            Scan again
          </Button>
        </div>

        {!pdfAvailable && (
          <p className="text-sm text-gray-500">The PDF couldn't be made this time. The full report still works.</p>
        )}
        {note && (
          <p role="alert" className="text-sm text-rag-red">
            {note}
          </p>
        )}

        <footer className="mt-12 space-y-1 border-t pt-4 text-xs text-gray-400">
          <p>
            {`Evidence ID: ${report.evidence_id ?? "Not available"} \u00b7 Engine: ${report.engine_version} \u00b7 Baseline: ${report.baseline_version}`}
          </p>
          {license && <p>{`Licensed to ${license.org} (${license.lic})`}</p>}
          {!report.scan.is_admin && <p>Scanned without admin rights.</p>}
          <p>Generated locally on this PC. Nothing was uploaded. Guidance only, not a full security audit.</p>
        </footer>
      </div>
    </div>
  );
}
