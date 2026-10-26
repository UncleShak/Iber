export default function ResultsScreen({ report, onScanAgain }: { report: any, onScanAgain: () => void }) {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Scan Results</h1>
      <p className="mb-4">Overall Status: {report?.overall || "Unknown"}</p>
      <button onClick={onScanAgain} className="bg-blue-600 text-white px-4 py-2 rounded">Scan Again</button>
    </div>
  );
}