"use client";

import { useCallback, useMemo, useState } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";

interface FileUploaderProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
  accept?: string;
  label?: string;
  hint?: string;
  maxSizeMB?: number;
}

const DEFAULT_ACCEPT = ".csv,.txt,.xlsx,.xls,.pdf";
const DEFAULT_MAX_SIZE = 10;

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function detectFormat(name: string): string {
  const ext = name.split(".").pop()?.toLowerCase();
  if (ext === "csv" || ext === "txt") {
    return "CSV";
  }
  if (ext === "xls" || ext === "xlsx") {
    return "Excel";
  }
  if (ext === "pdf") {
    return "PDF";
  }
  return "Unknown";
}

export default function FileUploader({
  onUpload,
  isUploading,
  accept = DEFAULT_ACCEPT,
  label = "Upload a file",
  hint = "CSV, Excel, or PDF up to 10 MB",
  maxSizeMB = DEFAULT_MAX_SIZE,
}: FileUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  const maxSize = useMemo(() => maxSizeMB * 1024 * 1024, [maxSizeMB]);

  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: FileRejection[]) => {
      if (fileRejections.length > 0) {
        setError(fileRejections[0]?.errors[0]?.message ?? "File rejected.");
        setSelectedFile(null);
        return;
      }

      const file = acceptedFiles[0];
      if (!file) {
        return;
      }

      const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
      const allowed = accept.split(",").map((value) => value.replace(".", "").trim());
      if (!allowed.includes(extension)) {
        setError("Unsupported file type. Please upload CSV, Excel, or PDF.");
        setSelectedFile(null);
        return;
      }

      if (file.size > maxSize) {
        setError(`File too large. Maximum size is ${maxSizeMB} MB.`);
        setSelectedFile(null);
        return;
      }

      setError("");
      setSelectedFile(file);
    },
    [accept, maxSize, maxSizeMB],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxSize,
    disabled: isUploading,
    multiple: false,
    accept: {
      "text/csv": [".csv"],
      "text/plain": [".txt"],
      "application/vnd.ms-excel": [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/pdf": [".pdf"],
    },
  });

  return (
    <section className="rounded-2xl border border-ink/10 bg-white/90 p-6 shadow">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-ink">{label}</p>
          <p className="mt-1 text-xs text-ink/60">{hint}</p>
        </div>
        <span className="rounded-full border border-ink/10 bg-ink/5 px-3 py-1 text-xs text-ink/60">
          Max {maxSizeMB} MB
        </span>
      </div>

      <div
        {...getRootProps()}
        className={`mt-4 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 py-8 text-center transition ${
          isDragActive ? "border-pine/60 bg-pine/5" : "border-ink/15 bg-white"
        } ${isUploading ? "opacity-60" : "hover:border-pine/40"}`}
      >
        <input {...getInputProps()} />
        <p className="text-sm font-semibold text-ink">
          {isDragActive ? "Drop the file here" : "Drag and drop a file here"}
        </p>
        <p className="mt-2 text-xs text-ink/60">Or click to browse your computer</p>
      </div>

      {selectedFile ? (
        <div className="mt-4 rounded-xl border border-ink/10 bg-ink/5 px-4 py-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-sm font-semibold text-ink">{selectedFile.name}</p>
              <p className="text-xs text-ink/60">
                {formatBytes(selectedFile.size)} · {detectFormat(selectedFile.name)}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setSelectedFile(null)}
              className="rounded-full border border-ink/15 px-3 py-1 text-xs text-ink/70 hover:border-ink/30"
              disabled={isUploading}
            >
              Clear
            </button>
          </div>
        </div>
      ) : null}

      {error ? <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

      <div className="mt-4 flex items-center justify-between">
        <p className="text-xs text-ink/60">Accepted: {accept}</p>
        <button
          type="button"
          onClick={() => selectedFile && onUpload(selectedFile)}
          disabled={!selectedFile || isUploading}
          className="rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-pine/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isUploading ? "Uploading..." : "Upload"}
        </button>
      </div>
    </section>
  );
}
