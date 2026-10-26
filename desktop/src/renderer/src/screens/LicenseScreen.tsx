export default function LicenseScreen({ onSuccess }: { onSuccess: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen p-4">
      <h1 className="text-2xl font-bold mb-4">Antigravity Cyber Health Check</h1>
      <p className="mb-4">A 1-minute, read-only check of this PC’s ransomware readiness.</p>
      <input type="text" placeholder="Enter License Key" className="border p-2 mb-4 w-64 text-black" />
      <button onClick={onSuccess} className="bg-blue-600 text-white px-4 py-2 rounded">Activate</button>
    </div>
  );
}