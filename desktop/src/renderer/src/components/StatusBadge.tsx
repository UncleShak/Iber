import { ShieldAlert, AlertTriangle, ShieldCheck, CircleSlash, CircleX } from "lucide-react";
import { cn } from "../lib/utils";

export default function StatusBadge({ status }: { status: string }) {
  const config = {
    red: { icon: ShieldAlert, text: "Act now", colors: "bg-rag-red-bg text-rag-red border-rag-red border" },
    amber: { icon: AlertTriangle, text: "Improve", colors: "bg-rag-amber-bg text-rag-amber border-rag-amber border" },
    green: { icon: ShieldCheck, text: "Good", colors: "bg-rag-green-bg text-rag-green border-rag-green border" },
    unavailable: { icon: CircleSlash, text: "Not checked", colors: "bg-rag-grey-bg text-rag-grey border-rag-grey border" },
    failed: { icon: CircleX, text: "Check failed", colors: "bg-rag-grey-bg text-rag-grey border-rag-grey border-dashed" }
  }[status] || { icon: CircleSlash, text: "Unknown", colors: "bg-gray-100 text-gray-500" };

  const Icon = config.icon;
  return (
    <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-sm font-medium", config.colors)}>
      <Icon className="w-4 h-4" /> {config.text}
    </span>
  );
}