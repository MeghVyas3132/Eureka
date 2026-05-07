"use client";

import axios from "axios";
import { FormEvent, useEffect, useState } from "react";

import { api } from "@/lib/api";

export type StoreType = "supermarket" | "convenience" | "specialty";

export interface StoreRecord {
  id: string;
  name: string;
  width_m: number;
  height_m: number;
  store_type: StoreType;
  created_at: string;
  updated_at: string;
}

interface NewStoreModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (store: StoreRecord) => void | Promise<void>;
}

const DEFAULT_FORM = {
  name: "",
  store_type: "supermarket" as StoreType,
  width_m: 50,
  height_m: 30,
};

export default function NewStoreModal({ isOpen, onClose, onCreated }: NewStoreModalProps) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setForm(DEFAULT_FORM);
      setError("");
      setLoading(false);
    }
  }, [isOpen]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await api.post<StoreRecord>("/api/v1/stores", {
        name: form.name.trim(),
        store_type: form.store_type,
        width_m: Number(form.width_m),
        height_m: Number(form.height_m),
      });
      await onCreated(response.data);
      onClose();
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (typeof detail === "string" && detail.trim().length > 0) {
          setError(detail);
        } else {
          setError("Unable to create store. Check the fields and try again.");
        }
      } else if (err instanceof Error && err.message.trim().length > 0) {
        setError(err.message);
      } else {
        setError("Unable to create store. Check the fields and try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-ink/10 bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-ink/50">New Store</p>
            <h2 className="mt-2 text-2xl font-semibold text-ink">Create a fresh space</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-ink/10 px-3 py-1 text-sm text-ink/70 transition hover:border-ink/30"
          >
            Close
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="block text-sm text-ink/70">
            Store name
            <input
              type="text"
              required
              value={form.name}
              onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
              className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-ink outline-none transition focus:border-pine/50 focus:ring-2 focus:ring-pine/20"
            />
          </label>

          <label className="block text-sm text-ink/70">
            Store type
            <select
              value={form.store_type}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, store_type: event.target.value as StoreType }))
              }
              className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-ink outline-none transition focus:border-pine/50 focus:ring-2 focus:ring-pine/20"
            >
              <option value="supermarket">Supermarket</option>
              <option value="convenience">Convenience</option>
              <option value="specialty">Specialty</option>
            </select>
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm text-ink/70">
              Width (m)
              <input
                type="number"
                min={1}
                max={1000}
                value={form.width_m}
                onChange={(event) => setForm((prev) => ({ ...prev, width_m: event.target.valueAsNumber }))}
                className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-ink outline-none transition focus:border-pine/50 focus:ring-2 focus:ring-pine/20"
              />
            </label>
            <label className="block text-sm text-ink/70">
              Height (m)
              <input
                type="number"
                min={1}
                max={1000}
                value={form.height_m}
                onChange={(event) => setForm((prev) => ({ ...prev, height_m: event.target.valueAsNumber }))}
                className="mt-2 w-full rounded-xl border border-ink/15 bg-white px-4 py-3 text-ink outline-none transition focus:border-pine/50 focus:ring-2 focus:ring-pine/20"
              />
            </label>
          </div>

          {error ? <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-pine px-4 py-3 text-sm font-semibold text-white transition hover:bg-pine/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Creating store..." : "Create store"}
          </button>
        </form>
      </div>
    </div>
  );
}
