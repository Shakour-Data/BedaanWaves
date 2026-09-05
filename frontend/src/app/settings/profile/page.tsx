"use client";

import { useEffect, useState } from "react";
import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useAuthStore } from "@/store/useAuthStore";
import { useUXStore } from "@/store/useUXStore";
import { cn } from "@/lib/cn";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { t } from "@/lib/i18n";
import type { UserProfile } from "@/store/useAuthStore";

export default function ProfilePage() {
  const { user } = useAuthStore();
  const addToast = useUXStore((state) => state.addToast);
  const [fullName, setFullName] = useState(user?.full_name || user?.username || "");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [confirmPasswordError, setConfirmPasswordError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setFullName(user.full_name || user.username || "");
    }
  }, [user]);

  const handleToggleShowPassword = () => {
    setShowPassword(!showPassword);
    setShowNewPassword(!showNewPassword);
  };

  const validatePasswords = (): boolean => {
    if (newPassword && confirmPassword && newPassword !== confirmPassword) {
      setConfirmPasswordError(t("app.settings.profile.error_password_match"));
      return false;
    }
    setConfirmPasswordError("");
    return true;
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validatePasswords()) return;
        
    setLoading(true);
    try {
      const response = await apiClient.patch("users/me", {
        full_name: fullName });
      
      if (response.status === 200) {
        const profile = await apiClient.get<UserProfile>('users/me');
        if (profile.data) {
          useAuthStore.setState({ user: profile.data });
        }
      } else {
        throw new Error(t("app.settings.profile.error_save"));
      }
    } catch (error) {
      addToast({ type: "error", message: getApiErrorMessage(error) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <NewDashboardShell title={t("app.settings.profile.title")}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-500">
        <Card icon="Profile" title={t("app.settings.profile.user_profile")} className="lg:col-span-3">
          <div className="flex items-center gap-6 py-2">
            <div className="w-24 h-24 rounded-full bg-neutral flex items-center justify-center text-4xl border-4 border-surface shadow-lg">
              Profile
            </div>
            <div className="flex-1">
              <h3 className="text-2xl font-black">{fullName || user?.full_name || user?.username || "User"}</h3>
              <p className="text-muted-foreground font-mono">{user?.email || "user@example.com"}</p>
              <div className="mt-3 flex gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-error/10 text-error border border-error/20">
                  {t("app.settings.profile.member_since").replace("{date}", "2023/01/01")}
                </span>
              </div>
            </div>
          </div>
        </Card>

        <Card icon="📄" title={t("app.settings.profile.account_info")} className="lg:col-span-1">
          <div className="space-y-6">
            <div>
              <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">{t("app.settings.profile.email")}</div>
              <span className="text-sm font-medium">{user?.email || "user@example.com"}</span>
            </div>

            <div>
              <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">{t("app.settings.profile.display_name")}</div>
              <span className="text-sm font-medium">{fullName}</span>
            </div>

            <div>
              <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">{t("app.settings.profile.login_status")}</div>
              <span className={cn(
                "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold",
                user?.is_active ? "bg-success/10 text-success" : "bg-error/10 text-error"
              )}>
                {user?.is_active ? t("app.settings.profile.active") : t("app.settings.profile.inactive")}
              </span>
            </div>

            <div>
              <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">{t("app.settings.profile.joined_date")}</div>
              <span className="text-sm font-medium">2023/01/01</span>
            </div>
          </div>
        </Card>

        <Card icon="🔐" title={t("app.settings.profile.security_settings")} className="lg:col-span-2">
          <form onSubmit={handleSave} className="space-y-6">
            <div>
              <label className="block text-sm font-bold mb-2">{t("app.settings.profile.full_name")}</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-xl px-4 py-3 border border-border bg-surface outline-none transition duration-fast ease-flow focus:border-error focus:ring-4 focus:ring-error/10"
              />
            </div>

            <div className="pt-4 border-t border-border/60">
              <h4 className="font-bold mb-4 flex items-center gap-2">
                <span>🔑</span> {t("app.settings.profile.change_password")}
              </h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2 relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    className="w-full rounded-xl px-4 py-3 border border-border bg-surface outline-none transition duration-fast ease-flow focus:border-error focus:ring-4 focus:ring-error/10 disabled:opacity-60"
                    placeholder="Current Password"
                  />
                  <button
                    type="button"
                    onClick={handleToggleShowPassword}
                    className={cn(
                      "absolute inset-y-0 flex items-center text-xl hover:text-error transition-colors",
                      false ? "left-4" : "right-4"
                    )}
                  >
                    {showPassword ? "👁️" : "👁️‍🗨️"}
                  </button>
                </div>

                <div className="space-y-4 md:col-span-2">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    disabled={loading}
                    className="w-full rounded-xl px-4 py-3 border border-border bg-surface outline-none transition duration-fast ease-flow focus:border-error focus:ring-4 focus:ring-error/10 disabled:opacity-60"
                    placeholder={t("app.settings.profile.new_password")}
                  />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    disabled={loading}
                    className="w-full rounded-xl px-4 py-3 border border-border bg-surface outline-none transition duration-fast ease-flow focus:border-error focus:ring-4 focus:ring-error/10 disabled:opacity-60"
                    placeholder={t("app.settings.profile.confirm_password")}
                  />
                </div>
              </div>
              
              {confirmPasswordError && (
                <p className="text-sm mt-3 text-error flex items-center gap-2 font-bold">
                  <span>⚠️</span> {confirmPasswordError}
                </p>
              )}
            </div>

            <div className="pt-4 flex justify-end">
              <Button
                type="submit"
                disabled={loading}
                className="w-full md:w-auto px-8"
              >
                {loading ? t("app.settings.profile.saving") : t("app.settings.profile.save_changes")}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </NewDashboardShell>
  );
}
