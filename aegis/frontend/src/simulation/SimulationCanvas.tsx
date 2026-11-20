import { useEffect, useRef, useState } from "react";
import type { EnvironmentInfo, RobotTelemetry, SensorFrame, WorldPoint } from "../types";
import { STATE_COLORS } from "../utils/format";

interface SimulationCanvasProps {
  env: EnvironmentInfo | null;
  telemetry: RobotTelemetry | null;
  sensors: SensorFrame | null;
  plannedPath: WorldPoint[];
  destination: WorldPoint | null;
  onMapClick: (worldX: number, worldY: number) => void;
}

const PADDING = 24;

export function SimulationCanvas({ env, telemetry, sensors, plannedPath, destination, onMapClick }: SimulationCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const traveled = useRef<WorldPoint[]>([]);
  const [size, setSize] = useState({ w: 800, h: 520 });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragRef = useRef<{ startX: number; startY: number; panX: number; panY: number } | null>(null);
  const draggedRef = useRef(false);
  // track a fading breadcrumb trail of the rover's completed route
  useEffect(() => {
    if (telemetry) {
      traveled.current.push({ x: telemetry.x, y: telemetry.y });
      if (traveled.current.length > 2000) traveled.current.shift();
    }
  }, [telemetry?.x, telemetry?.y]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setSize({ w: width, h: height });
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !env) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = size.w * dpr;
    canvas.height = size.h * dpr;
    canvas.style.width = `${size.w}px`;
    canvas.style.height = `${size.h}px`;
    ctx.scale(dpr, dpr);

    const scale = Math.min(
      (size.w - PADDING * 2) / env.width_m,
      (size.h - PADDING * 2) / env.height_m
    ) * zoom;

    const toPx = (x: number, y: number): [number, number] => [
      PADDING + x * scale + pan.x,
      PADDING + y * scale + pan.y,
    ];

    ctx.clearRect(0, 0, size.w, size.h);

    // -- grid ---------------------------------------------------------
    ctx.strokeStyle = "#1a1e21";
    ctx.lineWidth = 1;
    const step = 1;
    for (let gx = 0; gx <= env.width_m; gx += step) {
      const [x1, y1] = toPx(gx, 0);
      const [x2, y2] = toPx(gx, env.height_m);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
    for (let gy = 0; gy <= env.height_m; gy += step) {
      const [x1, y1] = toPx(0, gy);
      const [x2, y2] = toPx(env.width_m, gy);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }

    // -- world boundary -------------------------------------------------
    ctx.strokeStyle = "#33393e";
    ctx.lineWidth = 1.5;
    const [bx1, by1] = toPx(0, 0);
    const [bx2, by2] = toPx(env.width_m, env.height_m);
    ctx.strokeRect(bx1, by1, bx2 - bx1, by2 - by1);

    // -- axes labels (every 5m) ------------------------------------------
    ctx.fillStyle = "#5c666d";
    ctx.font = "10px monospace";
    for (let gx = 0; gx <= env.width_m; gx += 5) {
      const [x, y] = toPx(gx, 0);
      ctx.fillText(`${gx}`, x + 2, y + 10);
    }
    for (let gy = 5; gy <= env.height_m; gy += 5) {
      const [x, y] = toPx(0, gy);
      ctx.fillText(`${gy}`, x + 2, y + 10);
    }

    // -- obstacles ------------------------------------------------------
    for (const obs of env.obstacles) {
      const [x, y] = toPx(obs.x, obs.y);
      ctx.beginPath();
      ctx.arc(x, y, obs.radius * scale, 0, Math.PI * 2);
      ctx.fillStyle = obs.dynamic ? "rgba(224, 70, 63, 0.35)" : "rgba(90, 100, 110, 0.4)";
      ctx.fill();
      ctx.strokeStyle = obs.dynamic ? "#e0463f" : "#5c666d";
      ctx.lineWidth = 1.25;
      ctx.stroke();
    }

    // -- completed route (breadcrumb trail) ----------------------------
    if (traveled.current.length > 1) {
      ctx.beginPath();
      traveled.current.forEach((p, i) => {
        const [x, y] = toPx(p.x, p.y);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = "rgba(62, 207, 110, 0.5)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // -- planned path ----------------------------------------------------
    if (plannedPath.length > 1) {
      ctx.beginPath();
      plannedPath.forEach((p, i) => {
        const [x, y] = toPx(p.x, p.y);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = "#38b6d9";
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      for (const p of plannedPath) {
        const [x, y] = toPx(p.x, p.y);
        ctx.beginPath();
        ctx.arc(x, y, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = "#38b6d9";
        ctx.fill();
      }
    }

    // -- destination marker ------------------------------------------------
    if (destination) {
      const [x, y] = toPx(destination.x, destination.y);
      ctx.beginPath();
      ctx.moveTo(x, y - 9);
      ctx.lineTo(x + 8, y + 7);
      ctx.lineTo(x - 8, y + 7);
      ctx.closePath();
      ctx.strokeStyle = "#e0a730";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = "rgba(224, 167, 48, 0.15)";
      ctx.fill();
    }

    // -- rover + sensor arcs ---------------------------------------------
    if (telemetry) {
      const [rx, ry] = toPx(telemetry.x, telemetry.y);
      const headingRad = (telemetry.heading_deg * Math.PI) / 180;

      // lidar rays
      if (sensors) {
        ctx.strokeStyle = "rgba(56, 182, 217, 0.25)";
        ctx.lineWidth = 1;
        sensors.lidar_ranges.forEach((range, i) => {
          const angle = headingRad + (sensors.lidar_angles[i] * Math.PI) / 180;
          const ex = rx + Math.cos(angle) * range * scale;
          const ey = ry + Math.sin(angle) * range * scale;
          ctx.beginPath();
          ctx.moveTo(rx, ry);
          ctx.lineTo(ex, ey);
          ctx.stroke();
        });
      }

      // sensor range ring
      ctx.beginPath();
      ctx.arc(rx, ry, 8 * scale, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(56, 182, 217, 0.15)";
      ctx.lineWidth = 1;
      ctx.stroke();

      // body
      const bodyColor = STATE_COLORS[telemetry.state] ?? "#9aa4ab";
      ctx.save();
      ctx.translate(rx, ry);
      ctx.rotate(headingRad);
      const r = Math.max(8, 0.3 * scale);

      ctx.beginPath();
      ctx.arc(0, 0, r, 0, Math.PI * 2);
      ctx.fillStyle = "#181c1f";
      ctx.fill();
      ctx.strokeStyle = bodyColor;
      ctx.lineWidth = 2;
      ctx.stroke();

      // heading indicator (nose)
      ctx.beginPath();
      ctx.moveTo(r * 0.2, 0);
      ctx.lineTo(r * 1.5, 0);
      ctx.lineTo(r * 0.7, r * 0.5);
      ctx.moveTo(r * 1.5, 0);
      ctx.lineTo(r * 0.7, -r * 0.5);
      ctx.strokeStyle = bodyColor;
      ctx.lineWidth = 2;
      ctx.stroke();

      // simplified wheels
      ctx.fillStyle = "#0b0d0e";
      ctx.fillRect(-r * 0.3, -r * 1.15, r * 0.6, r * 0.35);
      ctx.fillRect(-r * 0.3, r * 0.8, r * 0.6, r * 0.35);
      ctx.restore();
    }
  }, [env, telemetry, sensors, plannedPath, destination, size, zoom, pan]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!env || draggedRef.current) return;
    const rect = canvasRef.current!.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    const scale = Math.min(
      (size.w - PADDING * 2) / env.width_m,
      (size.h - PADDING * 2) / env.height_m
    ) * zoom;
    const wx = (px - PADDING - pan.x) / scale;
    const wy = (py - PADDING - pan.y) / scale;
    if (wx >= 0 && wx <= env.width_m && wy >= 0 && wy <= env.height_m) {
      onMapClick(Math.round(wx * 10) / 10, Math.round(wy * 10) / 10);
    }
  };

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    setZoom((z) => Math.max(0.5, Math.min(3, z - e.deltaY * 0.001)));
  };

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden bg-grid" style={{ background: "var(--color-bg-inset)" }}>
      <canvas
        ref={canvasRef}
        onClick={handleClick}
        onWheel={handleWheel}
      onMouseDown={(e) => {
  dragRef.current = { startX: e.clientX, startY: e.clientY, panX: pan.x, panY: pan.y };
  draggedRef.current = false;
}}
onMouseMove={(e) => {
  if (!dragRef.current || e.buttons !== 1) return;
  const dx = e.clientX - dragRef.current.startX;
  const dy = e.clientY - dragRef.current.startY;
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
    draggedRef.current = true;
    setPan({ x: dragRef.current.panX + dx, y: dragRef.current.panY + dy });
  }
}}
onMouseUp={() => {
  dragRef.current = null;
}}
        className="cursor-crosshair"
      />
      <div
        className="absolute bottom-2 right-2 rounded border px-2 py-1 text-[10px] tabular-mono"
        style={{ background: "var(--color-bg-panel-raised)", borderColor: "var(--color-line)", color: "var(--color-text-tertiary)" }}
      >
        ZOOM {zoom.toFixed(1)}x · CLICK TO SET DESTINATION · SCROLL TO ZOOM · DRAG TO PAN
      </div>
    </div>
  );
}
