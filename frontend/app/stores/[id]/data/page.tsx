import { redirect } from "next/navigation";

interface StoreDataAliasPageProps {
  params: {
    id: string;
  };
  searchParams?: {
    tab?: string;
  };
}

export default function StoreDataAliasPage({ params, searchParams }: StoreDataAliasPageProps) {
  const tab = searchParams?.tab;
  const query = typeof tab === "string" && tab.length > 0 ? `?tab=${encodeURIComponent(tab)}` : "";
  redirect(`/store/${params.id}/data${query}`);
}
