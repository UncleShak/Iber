export default function ScanningScreen({ onCancel }: { onCancel: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen p-4">
      <h2 className="text-xl font-bold mb-4">Scanning...</h2>
      <p className="mb-4 text-gray-600">We only read settings. Nothing on your PC is changed.</p>
      <button onClick={onCancel} className="text-red-500 underline mt-4">Cancel Scan</button>
    </div>
  );
}