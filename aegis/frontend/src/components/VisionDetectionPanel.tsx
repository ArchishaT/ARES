import { useRef, useState } from "react";
import { Camera, Upload } from "lucide-react";
import { api } from "../services/api";
import type { VisionResult } from "../types";

export function VisionDetectionPanel() {
  const [result, setResult] = useState<VisionResult | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const runSimulated = async () => {
    setBusy(true);
    setError(null);
    try {
      setImageUrl(null);
      const res = await api.detectSimulated();
      setResult(res);
    } catch {
      setError("Vision inference failed.");
    } finally {
      setBusy(false);
    }
  };

  const handleUpload = async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      setImageUrl(URL.createObjectURL(file));
      const res = await api.detectUploaded(file);
      setResult(res);
    } catch {
      setError("Vision inference failed on uploaded frame.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2">
        <button
          onClick={runSimulated}
          disabled={busy}
          className="inline-flex items-center gap-1.5 rounded border px-3 py-1.5 text-xs uppercase tracking-wide"
          style={{ borderColor: "var(--color-line-strong)", color: "var(--color-text-primary)" }}
        >
          <Camera size={13} /> Use Simulated Camera
        </button>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={busy}
          className="inline-flex items-center gap-1.5 rounded border px-3 py-1.5 text-xs uppercase tracking-wide"
          style={{ borderColor: "var(--color-line-strong)", color: "var(--color-text-primary)" }}
        >
          <Upload size={13} /> Upload Image
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleUpload(f);
          }}
        />
      </div>

      {error && <div className="text-xs" style={{ color: "var(--color-status-fault)" }}>{error}</div>}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div
          className="relative aspect-video overflow-hidden rounded border"
          style={{ background: "var(--color-bg-inset)", borderColor: "var(--color-line)" }}
        >
          {imageUrl ? (
            <img src={imageUrl} alt="frame" className="h-full w-full object-contain" />
          ) : (
            <div className="flex h-full items-center justify-center text-xs" style={{ color: "var(--color-text-tertiary)" }}>
              {result ? "Simulated top-down camera frame" : "No frame processed yet"}
            </div>
          )}
          {result && result.objects.map((box, i) => {
            const scaleX = 100 / result.frame_width;
            const scaleY = 100 / result.frame_height;
            return (
              <div
                key={i}
                className="absolute border-2"
                style={{
                  left: `${box.x * scaleX}%`,
                  top: `${box.y * scaleY}%`,
                  width: `${box.width * scaleX}%`,
                  height: `${box.height * scaleY}%`,
                  borderColor: "var(--color-status-online)",
                }}
              >
                <span
                  className="absolute -top-4 left-0 whitespace-nowrap text-[10px] tabular-mono"
                  style={{ background: "var(--color-status-online-dim)", color: "var(--color-status-online)" }}
                >
                  {box.label} {(box.confidence * 100).toFixed(0)}%
                </span>
              </div>
            );
          })}
        </div>

        <div className="tabular-mono text-xs">
          <div className="mb-2 text-[10px] uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>
            Vision Status
          </div>
          {result ? (
            <div className="flex flex-col gap-1">
              <Row label="MODEL" value={result.model} />
              <Row label="OBJECTS" value={`${result.objects.length}`} />
              <Row label="INFERENCE" value={`${result.inference_time_ms.toFixed(1)} ms`} />
              <Row label="FRAME" value={`${result.frame_width}×${result.frame_height}`} />
              <Row label="STATUS" value="ACTIVE" tone="online" />
            </div>
          ) : (
            <div style={{ color: "var(--color-text-tertiary)" }}>Run a detection to see results.</div>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, tone }: { label: string; value: string; tone?: "online" }) {
  return (
    <div className="flex justify-between border-b py-1" style={{ borderColor: "var(--color-line-soft)" }}>
      <span style={{ color: "var(--color-text-tertiary)" }}>{label}</span>
      <span style={{ color: tone === "online" ? "var(--color-status-online)" : "var(--color-text-primary)" }}>{value}</span>
    </div>
  );
}
