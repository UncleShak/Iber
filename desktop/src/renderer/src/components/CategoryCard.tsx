import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import StatusBadge from "./StatusBadge";
import EvidenceTable from "./EvidenceTable";

export default function CategoryCard({ category }: { category: any }) {
  return (
    <Card id={category.id} className="mb-4">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">{category.title}</CardTitle>
        <StatusBadge status={category.status} />
      </CardHeader>
      <CardContent>
        <p className="text-sm text-gray-600 mb-2">{category.explanation}</p>
        <EvidenceTable evidence={category.evidence} />
      </CardContent>
    </Card>
  );
}