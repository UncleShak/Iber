export default function EvidenceTable({ evidence }: { evidence: any[] }) {
  if (!evidence.length) return null;
  return (
    <table className="w-full text-sm mt-3 border rounded-md overflow-hidden">
      <tbody className="divide-y">
        {evidence.map((row, i) => (
          <tr key={i} className={row.status === "unavailable" || row.status === "failed" ? "text-gray-400 italic" : "text-gray-700"}>
            <td className="py-2 px-3 font-medium bg-gray-50 w-1/3">{row.label}</td>
            <td className="py-2 px-3 w-2/3">{row.status === "failed" ? `Couldn't read: ${row.value}` : row.value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}