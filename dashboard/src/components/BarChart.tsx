import { useEffect, useRef } from "react";

export default function BarChart({ data, height = 180 }: {
  data: { label: string; income: number; expense: number }[];
  height?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.length) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const w = rect.width;
    const h = rect.height;
    ctx.clearRect(0, 0, w, h);

    const maxVal = Math.max(...data.flatMap(d => [d.income, d.expense])) || 1;
    const pad = { left: 8, right: 8, top: 10, bottom: 30 };
    const chartH = h - pad.top - pad.bottom;
    const barW = (w - pad.left - pad.right) / data.length;
    const bw = barW * 0.35;

    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 3; i++) {
      const y = pad.top + (chartH / 3) * i;
      ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
    }

    data.forEach((d, i) => {
      const x = pad.left + i * barW + barW / 2;
      const iH = (d.income / maxVal) * chartH;
      const eH = (d.expense / maxVal) * chartH;

      const incGrad = ctx.createLinearGradient(0, pad.top + chartH - iH, 0, pad.top + chartH);
      incGrad.addColorStop(0, "#10b981cc"); incGrad.addColorStop(1, "#10b98155");
      ctx.fillStyle = incGrad;
      ctx.beginPath();
      ctx.roundRect(x - bw - 2, pad.top + chartH - iH, bw, iH, [3, 3, 0, 0]);
      ctx.fill();

      const expGrad = ctx.createLinearGradient(0, pad.top + chartH - eH, 0, pad.top + chartH);
      expGrad.addColorStop(0, "#ef4444cc"); expGrad.addColorStop(1, "#ef444455");
      ctx.fillStyle = expGrad;
      ctx.beginPath();
      ctx.roundRect(x + 2, pad.top + chartH - eH, bw, eH, [3, 3, 0, 0]);
      ctx.fill();

      ctx.fillStyle = "rgba(255,255,255,0.35)";
      ctx.font = "10px Inter";
      ctx.textAlign = "center";
      ctx.fillText(d.label, x, h - 8);
    });
  }, [data, height]);

  return <canvas ref={canvasRef} style={{ width: "100%", height, display: "block" }} />;
}
