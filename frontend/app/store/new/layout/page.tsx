"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import NewStoreModal from "@/components/stores/NewStoreModal";

export default function NewLayoutPage() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(true);

  const handleClose = () => {
    setIsOpen(false);
    router.replace("/dashboard");
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_20%_0%,#f2e5c4_0%,#f6f7f8_45%,#eef2ef_100%)] px-6 py-8">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
        <header className="rounded-3xl border border-ink/10 bg-white/90 p-6 shadow">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/50">New layout</p>
          <h1 className="mt-2 text-3xl font-bold text-ink">Create a store first</h1>
          <p className="mt-2 text-sm text-ink/70">
            Layouts belong to a store. Create one now and we will open the layout builder.
          </p>
          <button
            type="button"
            onClick={() => setIsOpen(true)}
            className="mt-4 rounded-full bg-pine px-4 py-2 text-sm font-semibold text-white"
          >
            Create store
          </button>
        </header>
      </div>

      <NewStoreModal
        isOpen={isOpen}
        onClose={handleClose}
        onCreated={(store) => router.replace(`/store/${store.id}/layout`)}
      />
    </main>
  );
}
