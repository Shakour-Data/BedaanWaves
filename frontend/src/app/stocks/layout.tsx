import { NewDashboardShell } from "@/components/layout/NewDashboardShell";

export default function StocksLayout({ children }: { children: React.ReactNode }) {
  return <NewDashboardShell title="Stocks">{children}</NewDashboardShell>;
}
