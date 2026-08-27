import { NewDashboardShell } from "@/components/layout/NewDashboardShell";

export default function ScoringLayout({ children }: { children: React.ReactNode }) {
  return <NewDashboardShell title="AI Scoring">{children}</NewDashboardShell>;
}
