export function Spinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="w-8 h-8 rounded-full border-2 border-t-blue-500 animate-spin" style={{ borderColor: "var(--border-light)", borderTopColor: "#3b82f6" }} />
    </div>
  );
}

export function SkeletonCard({ h = "h-28" }: { h?: string }) {
  return <div className={`skeleton rounded-2xl ${h}`} />;
}

export function ErrorMsg({ msg }: { msg: string }) {
  return (
    <div className="text-center py-10">
      <p className="text-3xl mb-2">⚠️</p>
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>{msg}</p>
    </div>
  );
}
