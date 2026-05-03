"use client";

import { Fragment, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";

import type { ImportLogResponse } from "./types";

interface ImportHistoryProps {
  title: string;
  fetchUrl: string;
}

const STATUS_STYLES: Record<ImportLogResponse["status"], string> = {
  completed: "bg-green-100 text-green-700",
  partial: "bg-yellow-100 text-yellow-800",
  failed: "bg-red-100 text-red-700",
};

const FORMAT_LABELS: Record<ImportLogResponse["file_format"], string> = {
  csv: "CSV",
  excel: "Excel",
  pdf: "PDF",
};

export default function ImportHistory({ title, fetchUrl }: ImportHistoryProps) {
  const [rows, setRows] = useState<ImportLogResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const hasRows = rows.length > 0;

  useEffect(() => {
    let mounted = true;
    const fetchHistory = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await api.get<ImportLogResponse[]>(fetchUrl);
        if (mounted) {
          setRows(response.data);
        }
      } catch {
        if (mounted) {
          setError("Unable to load import history.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    void fetchHistory();

    return () => {
      mounted = false;
    };
  }, [fetchUrl]);

  const formatDate = useMemo(
    () => (value: string) => new Date(value).toLocaleString(),
    [],
  );

  if (loading) {
    return <p className="text-sm text-ink/60">Loading import history...</p>;
  }

  if (error) {
    return <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>;
  }

  if (!hasRows) {
    return <p className="text-sm text-ink/60">No imports recorded yet.</p>;
  }

  return (
    <section className="rounded-2xl border border-ink/10 bg-white/95 p-6 shadow">
      <h3 className="text-lg font-semibold text-ink">{title}</h3>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="bg-ink/5 text-xs uppercase tracking-widest text-ink/60">
            <tr>
              <th className="px-3 py-2">Date</th>
              <th className="px-3 py-2">File</th>
              <th className="px-3 py-2">Format</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Rows</th>
              <th className="px-3 py-2">Success</th>
              <th className="px-3 py-2">Errors</th>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const isExpanded = expandedId === row.id;
              return (
                <Fragment key={row.id}>
                  <tr
                    className="border-t border-ink/10 hover:bg-ink/5"
                    onClick={() => setExpandedId(isExpanded ? null : row.id)}
                  >
                    <td className="px-3 py-3 text-ink/70">{formatDate(row.imported_at)}</td>
                    <td className="px-3 py-3 font-semibold text-ink">{row.original_filename}</td>
                    <td className="px-3 py-3 text-ink/70">{FORMAT_LABELS[row.file_format]}</td>
                    <td className="px-3 py-3 text-ink/70">{row.import_type}</td>
                    <td className="px-3 py-3 text-ink/70">{row.total_rows}</td>
                    <td className="px-3 py-3 text-ink/70">{row.success_count}</td>
                    <td className="px-3 py-3 text-ink/70">{row.error_count}</td>
                    <td className="px-3 py-3">
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[row.status]}`}>
                        {row.status}
                      </span>
                    </td>
                  </tr>
                  {isExpanded ? (
                    <tr className="border-t border-ink/10 bg-ink/5">
                      <td colSpan={8} className="px-4 py-3 text-sm text-ink/70">
                        {row.error_detail && row.error_detail.length > 0 ? (
                          <div className="space-y-2">
                            <p className="text-xs uppercase tracking-widest text-ink/50">Errors</p>
                            <ul className="space-y-1">
                              {row.error_detail.map((errorRow) => (
                                <li key={`${row.id}-${errorRow.row}-${errorRow.reason}`}>
                                  Row {errorRow.row}: {errorRow.reason}
                                </li>
                              ))}
                            </ul>
                          </div>
                        ) : (
                          <p>No error details recorded.</p>
                        )}
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
