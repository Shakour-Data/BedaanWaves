"use client";

import { memo } from "react";
import { useAppStore } from "@/store/useAppStore";
import { useAuthStore } from "@/store/useAuthStore";
import { Sidebar } from "./Sidebar";

export const RightSidebar = memo(function RightSidebar() {
  const sidebarOpen = useAppStore((state) => state.rightSidebarOpen);
  const setSidebarOpen = useAppStore((state) => state.setRightSidebarOpen);
  const { user, logout } = useAuthStore();

  return (
    <Sidebar
      side="right"
      title="Quick Access"
      subtitle="Navigation"
      showSearch={false}
      showFooter={true}
      showUserInfo={!!user}
      onLogout={logout}
      sidebarOpen={sidebarOpen}
      setSidebarOpen={setSidebarOpen}
      closeOnLgOnly
    />
  );
});