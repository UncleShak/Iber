export default function App() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-900 p-8 text-center">
      <h1 className="text-4xl font-bold mb-4">Antigravity</h1>
      <p className="text-xl mb-8">A 1-minute, read-only check of this PC’s ransomware readiness.</p>
      
      <a href="#" className="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
        Download for Windows
      </a>
      
      <div className="mt-12 text-sm text-gray-500 space-y-2">
        <p>Runs on your PC. Reads settings only. Uploads nothing.</p>
        <p>To get a demo key, please ask our team at the stand.</p>
      </div>
    </div>
  );
}