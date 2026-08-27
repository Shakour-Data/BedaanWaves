"use client";

import { useEffect, useState } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import { cn } from "@/lib/cn";
import { apiClient } from "@/lib/api";
import { t } from "@/lib/i18n";

export default function ProfilePage() {
  const { user, currentLang } = useAuthStore();
  const [fullName, setFullName] = useState(user?.name || "");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [confirmPasswordError, setConfirmPasswordError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      // Sync with backend if needed
    }
  }, [user]);

  const handleToggleShowPassword = () => {
    setShowPassword(!showPassword);
    setShowNewPassword(!showNewPassword);
  };

  const validatePasswords = (): boolean => {
    if (newPassword && confirmPassword && newPassword !== confirmPassword) {
      setConfirmPasswordError(t("app.settings.profile.error_password_match", currentLang));
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
          const response = await apiClient.patch("/users/me", {
            full_name: fullName,
          });
          
          if (response.status === 200) {
            window.location.reload();
          } else {
            throw new Error(t("app.settings.profile.error_save", currentLang));
          }
          } catch (error) {
            // Handle error
          } finally {
          setLoading(false);
        }
      };

  return (
    <DashboardShell title={t("app.settings.profile.title", currentLang)}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-500">
        {/* User Profile */}
        <TarotCard icon="👤" title={t("app.settings.profile.user_profile", currentLang)} className="lg:col-span-3">
          <div className="flex items-center gap-6 py-2">
            <div className="w-24 h-24 rounded-full bg-neutral flex items-center justify-center text-4xl border-4 border-surface shadow-lg">
              👤
            </div>
            <div className="flex-1">
              <h3 className="text-2xl font-black">{fullName || user?.name || (currentLang === "fa" ? "کاربر" : "User")}</h3>
              <p className="text-muted-foreground font-mono">{user?.email || "user@example.com"}</p>
              <div className="mt-3 flex gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-red-600/10 text-red-600 border border-red-600/20">
                  {t("app.settings.profile.member_since", currentLang).replace("{date}", "۱۴۰۲/۰۱/۰۱")}
                </span>
              </div>
            </div>
          </div>
        </TarotCard>

        {/* Account Info */}
        <TarotCard icon="📄" title={t("app.settings.profile.account_info", currentLang)} className="lg:col-span-1">
          <div className="space-y-6">
            <div>
              <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">{t("app.settings.profile.email", currentLang)}</div>
              <span className="text-sm font-medium">{user?.email || "user@example.com"}</span>
            </div>

            <div>
              <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">{t("app.settings.profile.display_name", currentLang)}</div>
              <span className="text-sm font-medium">{fullName}</span>
            </div>

            <div>
              <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">{t("app.settings.profile.login_status", currentLang)}</div>
              <span className={cn(
                "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold",
                user?.isActive ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
              )}>
                {user?.isActive ? t("app.settings.profile.active", currentLang) : t("app.settings.profile.inactive", currentLang)}
              </span>
            </div>

            <div>
              <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">{t("app.settings.profile.joined_date", currentLang)}</div>
              <span className="text-sm font-medium">۱۴۰۲/۰۱/۰۱</span>
            </div>
          </div>
        </TarotCard>

        {/* Security Settings */}
        <TarotCard icon="🔐" title={t("app.settings.profile.security_settings", currentLang)} className="lg:col-span-2">
          <form onSubmit={handleSave} className="space-y-6">
            <div>
              <label className="block text-sm font-bold mb-2">{t("app.settings.profile.full_name", currentLang)}</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-xl px-4 py-3 border border-border bg-surface outline-none transition duration-fast ease-flow focus:border-red-600 focus:ring-4 focus:ring-red-600/10"
              />
            </div>

            <div className="pt-4 border-t border-border/60">
              <h4 className="font-bold mb-4 flex items-center gap-2">
                <span>🔑</span> {t("app.settings.profile.change_password", currentLang)}
              </h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2 relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    className="w-full rounded-xl px-4 py-3 border border-border bg-surface outline-none transition duration-fast ease-flow focus:border-red-600 focus:ring-4 focus:ring-red-600/10 disabled:opacity-60"
                    placeholder={currentLang === "fa" ? "رمز عبور فعلی" : "Current Password"}
                  />
                  <button
                    type="button"
                    onClick={handleToggleShowPassword}
                    className={cn(
                      "absolute inset-y-0 flex items-center text-xl hover:text-red-600 transition-colors",
                      currentLang === "fa" ? "left-4" : "right-4"
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
                    className="w-full rounded-xl px-4 py-3 border border-border bg-surface outline-none transition duration-fast ease-flow focus:border-red-600 focus:ring-4 focus:ring-red-600/10 disabled:opacity-60"
                    placeholder={t("app.settings.profile.new_password", currentLang)}
                  />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    disabled={loading}
                    className="w-full rounded-xl px-4 py-3 border border-border bg-surface outline-none transition duration-fast ease-flow focus:border-red-600 focus:ring-4 focus:ring-red-600/10 disabled:opacity-60"
                    placeholder={t("app.settings.profile.confirm_password", currentLang)}
                  />
                </div>
              </div>
              
              {confirmPasswordError && (
                <p className="text-sm mt-3 text-red-600 flex items-center gap-2 font-bold">
                  <span>⚠️</span> {confirmPasswordError}
                </p>
              )}
            </div>

            <div className="pt-4 flex justify-end">
              <PrimaryButton
                type="submit"
                disabled={loading}
                className="w-full md:w-auto px-8 shadow-lg shadow-red-600/20"
              >
                {loading ? t("app.settings.profile.saving", currentLang) : t("app.settings.profile.save_changes", currentLang)}
              </PrimaryButton>
            </div>
          </form>
        </TarotCard>
      </div>
    </DashboardShell>
  );
}
