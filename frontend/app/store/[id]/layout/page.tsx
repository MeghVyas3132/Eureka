"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

import { isUuid } from "@/lib/planogramRouting";

export default function StoreLayoutLegacyRedirectPage() {
  const params = useParams();
  const router = useRouter();
  const storeId = String(params?.id ?? "");

  useEffect(() => {
    if (!isUuid(storeId)) {
      router.replace("/stores/new/planogram");
      return;
    }

    router.replace(`/stores/${storeId}/planogram/latest`);
  }, [router, storeId]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-6 py-8">
      <p className="text-sm text-ink/70">Redirecting to the planogram editor...</p>
    </main>
  );
}
