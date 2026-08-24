"use client";

import { useEffect, useState } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { useAppStore } from "@/store/useAppStore";
import { useAuthStore } from "@/store/useAuthStore";
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

  const validatePasswords = (): boolean => {
    if (newPassword && confirmPassword && newPassword !== confirmPassword) {
      setConfirmPasswordError("رمز عبور جدید و تکرار آن باید یکسان باشند");
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
          const response = await apiClient.post("/user/profile/update", {
            full_name: fullName,
            new_password: newPassword,
          });
          
          if (response.status === 200) {
            // Success: refresh user data if needed
            window.location.reload();
          } else {
            throw new Error("بروز خطا در ذخیره اطلاعات");
          }
          } catch (error) {
            // Handle error (e.g., show toast)
          } finally {
          setLoading(false);
        }
      };

  return (
    <DashboardShell title="پروفایل کاربری">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* User Profile */}
        <TarotCard icon="" title="پروفایل کاربر" className="lg:col-span-3">
          <div className="flex items-start gap-4">
            <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center text-2xl">
              
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold">{fullName || user?.name || "کاربر نمایشی"}</h3>
              <p className="text-sm text-muted-foreground">{user?.email || "user@example.com"}</p>
              <div className="mt-2 flex gap-2">
                <span className="px-2 py-1 rounded text-xs bg-secondary text-secondary-foreground">
                  عضو از: ۱۴۰۲/۰۱/۰۱
                </span>
              </div>
            </div>
          </div>
        </TarotCard>

        {/* Account Info */}
        <TarotCard icon="" title="اطلاعات حساب" className="lg:col-span-2">
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
        <TarotCard icon="" title="تنظیمات امنیتی" className="lg:col-span-2">
          <div className="space-y-4">
            <div className="border-b border-border pb-2 mb-4">
              <div className="font-medium mb-2">تغییر رمز عبور</div>
              <div className="flex items-center gap-2">
                <span className="cursor-pointer mr-3">
                  <span className="text-xl">{showPassword ? "" : "️"}</span>
                </span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  className="flex-1 rounded-xl px-3 py-2 border border-border bg-surface px-3 py-2 outline-none transition duration-fast ease-flow focus:border-secondary focus:ring-2 focus:ring-secondary/20 disabled:opacity-60"
                />
              </div>
              <button
                type="button"
                onClick={handleToggleShowPassword}
                disabled={loading}
                className="ml-2 px-3 py-2 rounded-xl bg-secondary text-sm text-secondary hover:bg-primary/10 transition duration-fast ease-flow"
                aria-label={showPassword ? "مخفی کردن رمز" : "نمایش رمز"}
              >
                {showPassword ? "" : "️"}
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
                  <span className="text-xl">️</span>
                  {confirmPasswordError}
                </p>
              )}
            </div>

            <button
              type="submit"
              onClick={handleSave}
              disabled={loading}
              className="mt-4 w-full justify-center px-4 py-2 bg-secondary text-secondary-foreground hover:bg-secondary/20 transition duration-fast ease-flow"
            >
              {loading ? "در حال ذخیره..." : "ذخیره تغییرات"}
            </button>
          </div>
        </TarotCard>
      </div>
    </DashboardShell>
  );
}
