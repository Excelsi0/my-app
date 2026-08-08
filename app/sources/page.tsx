import type { Metadata } from "next";
import { DataSourcesOverview } from "@/components/data-sources-overview";

export const metadata: Metadata = {
  title: "Источники данных — ExFlow",
  description:
    "Финансовые API и сервис валютных курсов, которые ExFlow использует для расчёта выручки.",
};

export default function SourcesPage() {
  return <DataSourcesOverview />;
}
