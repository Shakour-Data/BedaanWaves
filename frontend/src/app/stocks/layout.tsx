import { DashboardShell } from "@/components/layout/DashboardShell";

export default function StocksLayout({ children }: { children: React.ReactNode }) {
  return <DashboardShell title="سهام">{children}</DashboardShell>;
}
