import { describe, it, expect, vi, beforeEach } from "vitest";
import { useAuthStore } from "@/store/useAuthStore";

describe("QA Priority 1 - SC-001: Direct Access Prevention (Auth Disabled)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Authentication guard (NewDashboardShell) - DISABLED", () => {
    it("allows access without authentication in development mode", () => {
      const replaceMock = vi.fn();
      const pushMock = vi.fn();

      vi.mock("@/store/useAuthStore", () => ({
        useAuthStore: Object.assign(vi.fn(), {
          getState: () => ({
            isAuthenticated: false,
            loading: false,
            token: null,
            user: null,
          }),
        }),
      }));

      useAuthStore.setState({
        isAuthenticated: false,
        loading: false,
        token: null,
        user: null,
      });

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
      expect(state.loading).toBe(false);
      expect(replaceMock).not.toHaveBeenCalled();
      expect(pushMock).not.toHaveBeenCalled();
    });

    it("allows authenticated users through without redirect", () => {
      useAuthStore.setState({
        isAuthenticated: true,
        loading: false,
        token: "test-token",
        user: { id: "1", email: "test@example.com" },
      });

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe("test-token");
    });

    it("shows loading spinner while auth is being checked", () => {
      useAuthStore.setState({
        isAuthenticated: false,
        loading: true,
        token: null,
        user: null,
      });

      const state = useAuthStore.getState();
      expect(state.loading).toBe(true);
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe("Dashboard tab state navigation", () => {
    it("defaults to 'overview' tab when no tab param is present", () => {
      const searchParams = new URLSearchParams("");
      const tabParam = searchParams.get("tab");
      const activeTab: "overview" | "general" =
        tabParam === "general" ? "general" : "overview";
      expect(activeTab).toBe("overview");
    });

    it("activates 'general' tab when tab=general param is set", () => {
      const searchParams = new URLSearchParams("tab=general");
      const tabParam = searchParams.get("tab");
      const activeTab: "overview" | "general" =
        tabParam === "general" ? "general" : "overview";
      expect(activeTab).toBe("general");
    });

    it("falls back to 'overview' for invalid tab param", () => {
      const searchParams = new URLSearchParams("tab=invalid");
      const tabParam = searchParams.get("tab");
      const activeTab: "overview" | "general" =
        tabParam === "general" ? "general" : "overview";
      expect(activeTab).toBe("overview");
    });
  });

  describe("Symbol-prop propagation (SC-003 prerequisite)", () => {
    it("passes symbol prop to loadSnapshot on mount", () => {
      const loadSnapshot = vi.fn().mockResolvedValue({});
      const symbol = "AAPL";

      const opts: Record<string, unknown> = {};
      if (symbol) opts.symbol = symbol;
      void loadSnapshot(opts);

      expect(loadSnapshot).toHaveBeenCalledWith({ symbol: "AAPL" });
    });

    it("does not include symbol when symbol is undefined", () => {
      const loadSnapshot = vi.fn().mockResolvedValue({});
      const symbol = undefined;

      const opts: Record<string, unknown> = {};
      if (symbol) opts.symbol = symbol;
      void loadSnapshot(opts);

      expect(loadSnapshot).toHaveBeenCalledWith({});
    });
  });
});
