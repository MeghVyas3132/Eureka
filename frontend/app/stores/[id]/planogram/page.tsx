import { redirect } from "next/navigation";

interface StorePlanogramEntryPageProps {
  params: {
    id: string;
  };
}

export default function StorePlanogramEntryPage({ params }: StorePlanogramEntryPageProps) {
  redirect(`/stores/${params.id}/planogram/latest`);
}
