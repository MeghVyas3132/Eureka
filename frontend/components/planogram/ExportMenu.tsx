"use client";

import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";

interface ExportMenuProps {
  planogramId: string | null;
  disabled?: boolean;
}

const FILENAME_FALLBACK = "planogram";

function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function filenameFromContentDisposition(header: string | undefined, fallback: string): string {
  if (!header) return fallback;
  const match = header.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? fallback;
}

export default function ExportMenu({ planogramId, disabled }: ExportMenuProps) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState<"jpeg" | "pptx" | null>(null);
  const [error, setError] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    if (open) {
      window.addEventListener("mousedown", onClick);
      return () => window.removeEventListener("mousedown", onClick);
    }
    return undefined;
  }, [open]);

  const handleDownload = async (format: "jpeg" | "pptx") => {
    if (!planogramId) return;
    setBusy(format);
    setError("");
    try {
      const response = await api.get(`/api/v1/planograms/${planogramId}/export/${format}`, {
        responseType: "blob",
      });
      const filename = filenameFromContentDisposition(
        response.headers["content-disposition"] as string | undefined,
        `${FILENAME_FALLBACK}.${format === "jpeg" ? "jpg" : "pptx"}`,
      );
      downloadBlob(response.data as Blob, filename);
      setOpen(false);
    } catch (err) {
      setError(`Unable to export ${format.toUpperCase()}.`);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        disabled={disabled || !planogramId}
        className="rounded-full border border-ink/20 px-4 py-2 text-sm font-semibold text-ink/80 transition hover:border-ink/40 disabled:opacity-40"
      >
        Export ▼
      </button>

      {open ? (
        <div className="absolute right-0 top-full z-30 mt-2 w-56 rounded-2xl border border-ink/10 bg-white p-2 shadow-lg">
          <button
            type="button"
            onClick={() => void handleDownload("jpeg")}
            disabled={busy !== null}
            className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm text-ink hover:bg-canvas/60 disabled:opacity-50"
          >
            <span>Export as JPEG</span>
            {busy === "jpeg" ? <span className="text-xs text-ink/50">...</span> : null}
          </button>
          <button
            type="button"
            onClick={() => void handleDownload("pptx")}
            disabled={busy !== null}
            className="flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm text-ink hover:bg-canvas/60 disabled:opacity-50"
          >
            <span>Export as PowerPoint</span>
            {busy === "pptx" ? <span className="text-xs text-ink/50">...</span> : null}
          </button>
          {error ? <p className="mt-1 px-3 pb-2 text-[11px] text-rose-600">{error}</p> : null}
        </div>
      ) : null}
    </div>
  );
}
