export default function Spinner({ text = "Memuat data..." }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
      <p className="text-slate-500 text-sm">{text}</p>
    </div>
  );
}

export function ErrorBox({ msg }: { msg: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-5 text-red-700 text-sm">
      <p className="font-semibold mb-1">Gagal memuat data</p>
      <p className="text-red-500">{msg}</p>
    </div>
  );
}
