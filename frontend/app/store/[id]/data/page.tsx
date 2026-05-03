"use client";

import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import ImportHistory from "@/components/ingestion/ImportHistory";
import DataFreshnessIndicator from "@/components/sales/DataFreshnessIndicator";
import ManualSalesEntry from "@/components/sales/ManualSalesEntry";
import SalesDataImporter from "@/components/sales/SalesDataImporter";

const TABS = [
  { key: "import", label: "Import file" },
  { key: "manual", label: "Manual entry" },
  { key: "history", label: "Import history" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

export default function StoreDataPage() {
  const params = useParams();
  const storeId = params?.id as string;
  const [activeTab, setActiveTab] = useState<TabKey>("import");

  const historyUrl = useMemo(
    () => `/api/v1/sales/import/history?store_id=${storeId}`,
    [storeId],
  );

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_20%_0%,#f2e5c4_0%,#f6f7f8_45%,#eef2ef_100%)] px-6 py-8">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <header className="rounded-3xl border border-ink/10 bg-white/90 p-6 shadow">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/50">Sales data</p>
          <h1 className="mt-2 text-3xl font-bold text-ink">Store data management</h1>
          <p className="mt-2 text-sm text-ink/70">Import files or enter manual sales records for this store.</p>
        </header>

        <div className="flex flex-wrap gap-3">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                activeTab === tab.key
                  ? "bg-pine text-white"
                  : "border border-ink/20 text-ink/70 hover:border-ink/40"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {activeTab === "import" ? (
          <div className="space-y-6">
            <DataFreshnessIndicator lastUpdated={null} />
            <SalesDataImporter storeId={storeId} />
          </div>
        ) : null}

        {activeTab === "manual" ? <ManualSalesEntry storeId={storeId} /> : null}

        {activeTab === "history" ? <ImportHistory title="Sales import history" fetchUrl={historyUrl} /> : null}
      </div>
    </main>
  );
}
