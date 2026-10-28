import { ShieldAlert } from "lucide-react";

export default function AdminHint() {
  return (
    <div className="bg-blue-50 text-blue-800 p-4 rounded-md flex gap-3 text-sm mb-8 text-left">
      <ShieldAlert className="w-5 h-5 flex-shrink-0" />
      <p>Tip: for a complete check, close this app, right-click it and choose <b>Run as administrator</b>.</p>
    </div>
  );
}