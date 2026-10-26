export default function ErrorScreen({ message, onTryAgain }: { message: string, onTryAgain: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen p-4">
      <h2 className="text-2xl font-bold text-red-600 mb-4">Something went wrong</h2>
      <p className="mb-4">{message}</p>
      <button onClick={onTryAgain} className="bg-gray-800 text-white px-4 py-2 rounded">Try Again</button>
    </div>
  );
}