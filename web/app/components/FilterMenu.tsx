"use client";

import { useEffect, useRef, useState } from "react";

export interface FilterItem {
  key: string;
  label: string;
  active: boolean;
}

export default function FilterMenu({
  ariaLabel,
  items,
  onToggle,
}: {
  ariaLabel: string;
  items: FilterItem[];
  onToggle: (key: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const activeCount = items.filter((i) => i.active).length;

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={wrapRef} style={{ position: "relative", display: "inline-block" }}>
      <button
        type="button"
        aria-label={ariaLabel}
        aria-haspopup="true"
        aria-expanded={open}
        aria-pressed={activeCount > 0}
        onClick={() => setOpen((v) => !v)}
        style={{ display: "flex", alignItems: "center", gap: 8 }}
      >
        <span>Filters{activeCount > 0 ? ` (${activeCount})` : ""}</span>
        <span aria-hidden style={{ fontSize: 10, opacity: 0.6 }}>▾</span>
      </button>
      {open && (
        <div
          role="menu"
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            zIndex: 20,
            padding: 4,
            minWidth: "100%",
            background: "rgba(255, 255, 255, 0.98)",
            border: "1px solid rgba(79, 110, 240, 0.35)",
            borderRadius: 10,
            boxShadow: "0 8px 24px rgba(80, 100, 160, 0.18)",
            backdropFilter: "blur(8px)",
          }}
        >
          {items.map((it) => (
            <button
              key={it.key}
              type="button"
              role="menuitemcheckbox"
              aria-checked={it.active}
              className={`dd-option${it.active ? " is-selected" : ""}`}
              onClick={() => onToggle(it.key)}
            >
              {it.active ? "✓ " : ""}
              {it.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
