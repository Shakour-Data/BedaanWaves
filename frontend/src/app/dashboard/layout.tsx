"use client";

import { NewDashboardShell } from "@/components/layout/NewDashboardShell";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <NewDashboardShell title="Dashboard">
      {children}
    </NewDashboardShell>
  );
}
