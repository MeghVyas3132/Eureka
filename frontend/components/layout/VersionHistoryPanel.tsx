"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Layout, LayoutVersionSummary } from "@/store/canvasStore";

interface VersionHistoryPanelProps {
  layoutId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onRestored: (layout: Layout) => void;
}

interface VersionListResponse {
  data: LayoutVersionSummary[];
}

export default function VersionHistoryPanel({
  layoutId,
  isOpen,
  onClose,
  onRestored,
}: VersionHistoryPanelProps) {
  const [versions, setVersions] = useState<LayoutVersionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isOpen || !layoutId) {
      return;
    }

    const fetchVersions = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await api.get<VersionListResponse>(`/api/v1/layouts/${layoutId}/versions`);
        setVersions(response.data.data);
      } catch {
        setError("Unable to load version history.");
      } finally {
        setLoading(false);
      }
    };

    void fetchVersions();
  }, [isOpen, layoutId]);

  const handleRestore = async (versionId: string) => {
    if (!layoutId) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await api.post<Layout>(`/api/v1/layouts/${layoutId}/rollback/${versionId}`);
      onRestored(response.data);
      onClose();
    } catch {
      setError("Unable to restore this version.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`fixed inset-0 z-40 ${isOpen ? "" : "pointer-events-none"}`}>
      <div
        className={`absolute inset-0 bg-ink/30 transition-opacity ${isOpen ? "opacity-100" : "opacity-0"}`}
        onClick={onClose}
      />
      <aside
        className={`absolute right-0 top-0 h-full w-full max-w-sm transform border-l border-ink/10 bg-white/95 p-6 shadow-2xl transition-transform ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-ink/50">History</p>
            <h3 className="mt-2 text-xl font-semibold text-ink">Layout Versions</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-ink/15 px-3 py-1 text-sm text-ink/70 transition hover:border-ink/30"
          >
            Close
          </button>
        </div>

        {error ? <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

        {loading ? (
          <p className="mt-6 text-sm text-ink/60">Loading versions...</p>
        ) : versions.length === 0 ? (
          <p className="mt-6 text-sm text-ink/60">No saved versions yet.</p>
        ) : (
          <div className="mt-6 space-y-3">
            {versions.map((version) => (
              <div key={version.id} className="rounded-xl border border-ink/10 bg-white p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-ink">Version {version.version_number}</p>
                    <p className="text-xs text-ink/60">
                      {new Date(version.created_at).toLocaleString()}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void handleRestore(version.id)}
                    className="rounded-lg border border-pine/30 px-3 py-2 text-xs font-semibold text-pine transition hover:bg-pine/10"
                  >
                    Restore
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </aside>
    </div>
  );
}
