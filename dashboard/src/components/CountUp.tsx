import { useEffect, useRef, useState } from "react";

export default function CountUp({ value, prefix = "", suffix = "", duration = 1200 }: {
  value: number; prefix?: string; suffix?: string; duration?: number;
}) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<number>(0);
  const startRef = useRef<number>(0);

  useEffect(() => {
    const start = performance.now();
    startRef.current = 0;
    const target = value;
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(eased * target));
      if (progress < 1) ref.current = requestAnimationFrame(animate);
    };
    ref.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(ref.current);
  }, [value, duration]);

  const neg = display < 0;
  const abs = Math.abs(display);
  const formatted = abs >= 1_000_000
    ? (abs / 1_000_000).toFixed(1) + " jt"
    : abs >= 1_000
    ? abs.toLocaleString("id-ID")
    : String(abs);

  return (
    <span className="count-animate tabular-nums">
      {prefix}{neg ? "-" : ""}{formatted}{suffix}
    </span>
  );
}
