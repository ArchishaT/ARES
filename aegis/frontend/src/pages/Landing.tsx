import { useEffect, useRef } from "react";

interface LandingProps {
  onEnter: () => void;
}

export function Landing({ onEnter }: LandingProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    let raf = 0;
    let t = 0;

    const resize = () => {
      canvas.width = canvas.offsetWidth * devicePixelRatio;
      canvas.height = canvas.offsetHeight * devicePixelRatio;
      ctx.scale(devicePixelRatio, devicePixelRatio);
    };
    resize();

    const nodes = Array.from({ length: 40 }, () => ({
      x: Math.random() * canvas.offsetWidth,
      y: Math.random() * canvas.offsetHeight,
      vx: (Math.random() - 0.5) * 0.15,
      vy: (Math.random() - 0.5) * 0.15,
    }));

    const draw = () => {
      t += 1;
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      ctx.clearRect(0, 0, w, h);

      ctx.strokeStyle = "rgba(56, 182, 217, 0.06)";
      ctx.lineWidth = 1;
      const gridSize = 40;
      for (let x = 0; x < w; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
      }
      for (let y = 0; y < h; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      for (const n of nodes) {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > w) n.vx *= -1;
        if (n.y < 0 || n.y > h) n.vy *= -1;
      }
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const d = Math.hypot(dx, dy);
          if (d < 140) {
            ctx.strokeStyle = `rgba(56, 182, 217, ${0.12 * (1 - d / 140)})`;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
        ctx.fillStyle = "rgba(56, 182, 217, 0.5)";
        ctx.beginPath();
        ctx.arc(nodes[i].x, nodes[i].y, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }

      raf = requestAnimationFrame(draw);
    };
    draw();

    const onResize = () => resize();
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <div className="relative flex h-screen w-full items-center justify-center overflow-hidden" style={{ background: "var(--color-bg-void)" }}>
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
      <div className="relative z-10 flex flex-col items-center text-center px-6">
        <div className="mb-6 flex h-14 w-14 items-center justify-center rounded border" style={{ borderColor: "var(--color-status-nav)" }}>
          <div className="h-4 w-4" style={{ background: "var(--color-status-nav)", clipPath: "polygon(50% 0%, 0% 100%, 100% 100%)" }} />
        </div>
        <h1 className="text-5xl font-bold tracking-[0.2em]" style={{ color: "var(--color-text-primary)" }}>
          AEGIS
        </h1>
        <div className="mt-3 text-xs font-medium uppercase tracking-[0.35em]" style={{ color: "var(--color-status-nav)" }}>
          Autonomous Robotics Command System
        </div>
        <p className="mt-6 tabular-mono text-sm" style={{ color: "var(--color-text-secondary)" }}>
          Simulate. Navigate. Detect. Adapt.
        </p>
        <button
          onClick={onEnter}
          className="mt-10 rounded border px-8 py-3 text-xs font-semibold uppercase tracking-[0.25em] transition-colors hover:brightness-110"
          style={{ borderColor: "var(--color-status-nav)", background: "var(--color-status-nav-dim)", color: "var(--color-status-nav)" }}
        >
          Enter Mission Control
        </button>
        <div className="mt-8 tabular-mono text-[10px]" style={{ color: "var(--color-text-tertiary)" }}>
          A* PATH PLANNING · LIDAR/ULTRASONIC SIMULATION · REAL-TIME TELEMETRY · COMPUTER VISION
        </div>
      </div>
    </div>
  );
}
