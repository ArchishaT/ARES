import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { api } from "../services/api";
import type { NoteItem } from "../types";

export function NotesPanel() {
  const [notes, setNotes] = useState<NoteItem[]>([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");

  const refresh = () => api.listNotes().then(setNotes).catch(() => void 0);
  useEffect(() => {
    refresh();
  }, []);

  const save = async () => {
    if (!title.trim() && !body.trim()) return;
    await api.createNote(title || "Untitled", body);
    setTitle("");
    setBody("");
    refresh();
  };

  return (
    <div className="flex flex-col gap-3">
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Note title (e.g. Round 3 — blue team debrief)"
        className="rounded border px-2 py-1 text-xs"
        style={{ background: "var(--color-bg-inset)", borderColor: "var(--color-line)", color: "var(--color-text-primary)" }}
      />
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Observations, findings, follow-ups…"
        rows={3}
        className="rounded border px-2 py-1 text-xs"
        style={{ background: "var(--color-bg-inset)", borderColor: "var(--color-line)", color: "var(--color-text-primary)" }}
      />
      <button
        onClick={save}
        className="self-start rounded border px-3 py-1 text-[11px] uppercase tracking-wide"
        style={{ borderColor: "var(--color-status-nav)", color: "var(--color-status-nav)" }}
      >
        Save Note
      </button>

      <div className="mt-1 flex flex-col gap-2 max-h-64 overflow-y-auto">
        {notes.length === 0 && (
          <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>No notes yet.</div>
        )}
        {notes.slice().reverse().map((n) => (
          <div key={n.id} className="rounded border px-2 py-1.5" style={{ borderColor: "var(--color-line)", background: "var(--color-bg-inset)" }}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium" style={{ color: "var(--color-text-primary)" }}>{n.title}</span>
              <button onClick={() => api.deleteNote(n.id).then(refresh)} style={{ color: "var(--color-text-tertiary)" }}>
                <Trash2 size={12} />
              </button>
            </div>
            {n.body && <p className="mt-1 text-[11px]" style={{ color: "var(--color-text-secondary)" }}>{n.body}</p>}
            <div className="mt-1 text-[10px] tabular-mono" style={{ color: "var(--color-text-tertiary)" }}>{n.created_at}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
