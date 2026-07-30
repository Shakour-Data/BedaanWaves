"use client";

import { useEffect, useState } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { useAppStore } from "@/store/useAppStore";
import { useAuthStore } from "@/store/useAuthStore";
import { cn } from "@/lib/cn";

export default function SettingsPage() {
  const { theme, setTheme } = useAppStore();
  const { user } = useAuthStore();
  const [allPreferences, setAllPreferences] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function loadPreferences() {
      setLoading(true);
      try {
        // Load user preferences
        const prefsRes = await apiClient.get<any>("/preferences?user_id=" + (user?.id || "current"));
        
        if (active) {
          const prefsData = prefsRes.data || [];
          const preferences = [
            { id: "theme", label: "تم‌بندی", value: theme, options: ["light", "dark"], current: theme },
            { id: "region", label: "محل جغرافیایی", value: prefsData.region || "IR", options: ["IR", "US", "EU", "CA"] },
            { id: "language", label: "زبان", value: prefsData.language || "fa", options: ["fa", "en", "tr"] },
            { id: "notifications_email", label: "پوشCollect e-mail", value: prefsData.notifications_email || true },
            { id: "notifications_push", label: "پوشCollect ادشاری", value: prefsData.notifications_push || true },
            { id: "default_symbols", label: "نمادهای پیش‌فرض", value: prefsData.default_symbols || ["فولاد", "کناره", "بیت‌کوین"] },
          ];
          
          setAllPreferences(preferences);
        }
      } catch (error) {
        console.error("Failed to load preferences:", error);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadPreferences();
    return () => { active = false; };
  }, []);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    // Implement save logic here
    console.log("Saving preferences");
  };

  if (loading) {
    return (
      <DashboardShell title="تنظیمات">
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          در حال بارگذاری تنظیمات...
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title="تنظیمات">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* User Profile */}
        <TarotCard icon="👤" title="پروفایل کاربر" className="lg:col-span-3">
          {user && (
            <div className="flex items-start gap-4">
              <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center text-2xl">
                👤
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold">{user.name || "کاربر نمایشی"}</h3>
                <p className="text-sm text-muted-foreground">{user.email || "user@example.com"}</p>
                <div className="mt-2 flex gap-2">
                  <span className="px-2 py-1 rounded text-xs bg-secondary text-secondary-foreground">
                    عضو از: ۱۴۰۲/۰۱/۰۱
                  </span>
                </div>
              </div>
            </div>
          </TarotCard>

          {/* Theme Settings */}
          <TarotCard icon="🎨" title="تنظیمات ظاهری">
            <div className="space-y-4">
              {Array.from(Object.keys(preferencesOptions || {})).map((id) => {
                const preference = allPreferences.find((p) => p.id === id);
                if (!preference) return null;
                return (
                  <div key={id} className="space-y-3 mb-4">
                    <div className="font-medium mb-1">{preference.label}</div>
                    <div className="grid grid-cols-2 gap-3">
                      {preference.options?.map((opt) => {
                        const isSelected = preference.value === opt;
                        return (
                          <label key={opt} className="flex items-center gap-2">
                            <input
                              type="radio"
                              name={id}
                              value={opt}
                              checked={isSelected}
                              onChange={(e) => {
                                if (/theme|region|language/.test(id)) {
                                  setTheme(opt as any);
                                }
                              }}
                            />
                            <span>{opt}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </TarotCard>

          {/* Notification Settings */}
          <TarotCard icon="🔔" title="تنظیمات اعلان‌ها">
            <div className="space-y-4">
              {preferencesOptions.map((id) => {
                const preference = allPreferences.find((p) => p.id === id);
                if (!preference) return null;
                return (
                  <div key={id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                    <div className="flex items-center gap-3">
                      <span className="font-medium">{preference.label}</span>
                    </div>
                    <label className="relative inline-block cursor-pointer">
                      <input
                        type="checkbox"
                        defaultChecked={Boolean(preference?.value)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-success"></div>
                    </label>
                  </div>
                );
              })}
            </div>
          </TarotCard>

          {/* Quick Actions */}
          <TarotCard icon="⚡" title="عملیات سریع">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[].map((action, i) => (
                <button
                  key={i}
                  className="p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors text-center"
                >
                  {action.icon || "?"}
                </button>
              ))}
            </div>
          </TarotCard>

          {/* System Info */}
          <TarotCard icon="🖥️" title="اطلاعات سیستم" className="lg:col-span-3">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[].map((stat, i) => (
                <div key={i} className="text-center">
                  {/* Placeholder for system stats */}
                </div>
              ))}
            </div>
          </TarotCard>
        </div>
      </div>
    </DashboardShell>
  );
}

const preferencesOptions

<tool_call>
<function=write>
<parameter=content>
"use client";

import { useEffect, useState } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { cn } from "@/lib/cn";
import { apiClient } from "@/lib/api";

export default function ProfilePage() {
  const { user } = useAuthStore();
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

  const validatePasswords = () => {
    if (newPassword && confirmPassword && newPassword !== confirmPassword) {
      setConfirmPasswordError("رمز عبور جدید و تکرار آن باید یکسان باشند");
    } else {
      setConfirmPasswordError("");
    }
  };

  return (
    <DashboardShell title="پروفایل کاربری">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* User Profile */}
        <TarotCard icon="👤" title="پروفایل کاربر" className="lg:col-span-3">
          <div className="flex items-start gap-4">
            <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center text-2xl">
              👤
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold">{fullName || user?.name || "کاربر نمایشی"}</h3>
              <p className="text-sm text-muted-foreground">به آWord: {user?.email}</p>
              <div className="mt-2 flex gap-2">
                <span className="px-2 py-1 rounded text-xs bg-secondary text-secondary-foreground">
                  عضو از: ۱۴۰۲/۰۱/۰۱
                </span>
              </div>
            </div>
          </div>
        </TarotCard>

        {/* Account Info */}
        <TarotCard icon="🌐" title="اطلاعات حساب" className="lg:col-span-2">
          <div className="space-y-4">
            <div>
              <div className="text-sm font-medium mb-2">ایمیل</div>
              <span className="text-sm text-muted-foreground">{user?.email || "user@example.com"}</span>
            </div>

            <div>
              <div className="text-sm font-medium mb-2">نام نمایشی</div>
              <span className="text-sm text-muted-foreground">{fullName}</span>
            </div>

            <div>
              <div className="text-sm font-medium mb-2">وضعیت ورود</div>
              <span className="text-sm text-muted-foreground">{user?.isActive ? "فعال" : "غیرفعال"}</span>
            </div>

            <div>
              <div className="text-sm font-medium mb-2">تاریخ ثبت‌نام</div>
              <span className="text-sm text-muted-foreground">۱۴۰۲/۰۱/۰۱</span>
            </div>
          </div>
        </TarotCard>

        {/* Security Settings */}
        <TarotCard icon="🔒" title="تنظیمات امنیتی" className="lg:col-span-2">
          <div className="space-y-4">
            <div className="border-b border-border pb-2 mb-4">
              <div className="font-medium mb-2">تغییر رمز عبور</div>
              <div className="flex items-center gap-2">
                <span className="cursor-pointer mr-3">
                  <span className="text-xl">{showPassword ? "🙈" : "👁️"}</span>
                </span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  className="flex-1 rounded-xl px-3 py-2 border border-border text-sm outline-none transition duration-fast ease-flow focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              />
            </div>
            <button
              type="button"
              onClick={handleToggleShowPassword}
              disabled={loading}
              className="ml-2 px-3 py-2 rounded-xl bg-secondary text-sm text-secondary hover:bg-primary/10 transition duration-fast ease-flow"
              aria-label={showPassword ? "مخفی کردن رمز" : "نمایش رمز"}
            >
              {showPassword ? "🙈" : "👁️"}
            </button>
          </div>

          <div>
            <div className="font-medium mb-2">رمز عبور جدید</div>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              disabled={loading}
              className="flex-1 rounded-xl px-3 py-2 border border-border bg-surface px-3 py-2 outline-none transition duration-fast ease-flow focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              placeholder="حداقل ۸ کاراکتر"
            />
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={loading}
              className="flex-1 rounded-xl px-3 py-2 border border-border bg-surface px-3 py-2 outline-none transition duration-fast ease-flow focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
              placeholder="تکرار رمز جدید"
            />
            {confirmPasswordError && (
              <p className="text-sm mt-1 text-primary flex items-center">
                <span className="text-xl">⚠️</span>
                {confirmPasswordError}
              </p>
            )}
          </div>

          <PrimaryButton type="submit" disabled={loading} className="mt-4 w-full justify-center">
            {loading ? "در حال ذخیره..." : "ذخیره تغییرات"}
          </PrimaryButton>
        </TarotCard>
      </div>
    </DashboardShell>
  );
}