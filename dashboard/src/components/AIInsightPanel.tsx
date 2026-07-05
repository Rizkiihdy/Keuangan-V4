import { useEffect, useState } from "react";
import { fetchAiInsight } from "../api/client";

export default function AIInsightPanel() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAiInsight().then(setData).finally(() => setLoading(false));
  }, []);

  return (
    <div className="card p-5">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base"
          style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>✨</div>
        <div>
          <h3 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>Oliv AI Insight</h3>
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>Analisis otomatis oleh Gemini AI</p>
        </div>
        {data?.generated_at && (
          <span className="ml-auto text-xs px-2 py-1 rounded-lg" style={{ background: "rgba(99,102,241,0.1)", color: "#818cf8" }}>
            Live
          </span>
        )}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="skeleton h-6 rounded-lg" />)}
        </div>
      ) : (
        <div className="space-y-3">
          {data?.insights?.map((line: string, i: number) => (
            <div key={i} className="flex gap-3 p-3 rounded-xl text-sm"
              style={{ background: "rgba(255,255,255,0.03)", color: "var(--text-secondary)" }}>
              <span>{line}</span>
            </div>
          ))}
          {data?.error && (
            <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
              💡 Insight dari template (API error)
            </p>
          )}
        </div>
      )}
    </div>
  );
}
