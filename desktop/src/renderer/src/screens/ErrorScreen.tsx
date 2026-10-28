import { Button } from "../components/ui/button";
import { AlertTriangle } from "lucide-react";

export default function ErrorScreen({ message, onTryAgain }: { message: string, onTryAgain: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 text-center">
      <AlertTriangle className="w-12 h-12 text-rag-red mb-4" />
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong</h2>
      <p className="mb-8 text-gray-600 max-w-md">{message}</p>
      <Button onClick={onTryAgain} variant="default">Try Again</Button>
      <p className="text-xs text-gray-400 mt-6">Details saved to a log file.</p>
    </div>
  );
}