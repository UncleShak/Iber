import { Button } from "../components/ui/button";
import { Separator } from "../components/ui/separator";
import StatusBadge from "../components/StatusBadge";
import CategoryCard from "../components/CategoryCard";
import FixList from "../components/FixList";
import { FileText, Download } from "lucide-react";

export default function ResultsScreen({ report, onScanAgain }: { report: any, onScanAgain: () => void }) {
  const topFixes = report.top_fixes.map((id: string) => report.fixes.find((f: any) => f.id === id));

  return (
    <div className="min-h-screen bg-rag-grey-bg p-8 text-rag-grey pb-24">
      <div className="max-w-4xl mx-auto space-y-6">
        
        <header className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2 text-black">Scan Results</h1>
            <p className="text-lg text-gray-700">{report.summary}</p>
          </div>
          <StatusBadge status={report.overall} />
        </header>

        <FixList fixes={topFixes} />

        <Separator className="my-8" />
        
        <section>
          {report.categories.map((c: any) => <CategoryCard key={c.id} category={c} />)}
        </section>

        <div className="flex gap-4 mt-8 flex-wrap">
          <Button onClick={() => window.antigravity.openPdf(report.run_id)}><FileText className="w-4 h-4 mr-2"/> Open one-page action plan (PDF)</Button>
          <Button variant="outline" onClick={() => window.antigravity.openHtml(report.run_id)}>Open full report</Button>
          <Button variant="secondary" onClick={() => window.antigravity.exportEvidence(report.run_id)}><Download className="w-4 h-4 mr-2"/> Export evidence for insurer</Button>
          <div className="flex-1" />
          <Button variant="ghost" onClick={onScanAgain}>Scan Again</Button>
        </div>

        <footer className="mt-12 text-xs text-gray-400 border-t pt-4 space-y-1">
          <p>Evidence ID: {report.evidence_id || "Not available"} · Engine: {report.engine_version} · Baseline: {report.baseline_version}</p>
          {!report.scan.is_admin && <p>Scanned without admin rights.</p>}
          <p>Generated locally on this PC. Nothing was uploaded. Guidance only, not a full security audit.</p>
        </footer>

      </div>
    </div>
  );
}