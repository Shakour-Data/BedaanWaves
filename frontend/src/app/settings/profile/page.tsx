"use client";

import { useEffect, useState } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useAuthStore } from "@/store/useAuthStore";
import { apiClient } from "@/lib/api";
import { FaEyeIcon, FaEyeSlashIcon } from "@/app/reset-password/icons";

export default function ProfilePage() {
  const { user } = useAuthStore();
  const { isAuthenticated } = useAuthStore();
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
      setFullName(user.name || "");
    }
  }, [user]);

  const validatePasswords = (): boolean => {
    if (newPassword && confirmPassword && newPassword !== confirmPassword) {
      setConfirmPasswordError("رمز عبور جدید و تکرار آن باید یکسان باشند");
      return false;
    }
    setConfirmPasswordError("");
    return true;
  };

  const [saveError, setSaveError] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveError(null);
    if (!validatePasswords()) return;
    setLoading(true);
    try {
      const response = await apiClient.patch("/users/me", {
        full_name: fullName,
      });

      if (response.status === 200) {
        window.location.reload();
      } else {
        throw new Error("بروز خطا در ذخیره اطلاعات");
      }
    } catch (error) {
      setSaveError("خطا در ذخیره اطلاعات. لطفاً دوباره تلاش کنید.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardShell title="پروفایل کاربری">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* User Profile */}
        <TarotCard title="پروفایل کاربر" className="lg:col-span-3">
          <div className="flex items-start gap-4">
            <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center text-2xl">
              {user?.name?.charAt(0) || "U"}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold">{fullName || user?.name || "کاربر نمایشی"}</h3>
              <p className="text-sm text-muted-foreground">{user?.email || "user@example.com"}</p>
              <div className="mt-2 flex gap-2">
                <span className="px-2 py-1 rounded text-xs bg-secondary text-secondary-foreground">
                  عضو از: {user?.created_at ? new Date(user.created_at).toLocaleDateString("fa-IR") : "—"}
                </span>
              </div>
            </div>
          </div>
        </TarotCard>

        {/* Account Info */}
        <TarotCard title="اطلاعات حساب" className="lg:col-span-2">
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
              <span className="text-sm text-muted-foreground">{isAuthenticated ? "فعال" : "غیرفعال"}</span>
            </div>

            <div>
              <div className="text-sm font-medium mb-2">تاریخ ثبت‌نام</div>
              <span className="text-sm text-muted-foreground">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString("fa-IR") : "—"}
              </span>
            </div>
          </div>
        </TarotCard>

        {/* Security Settings */}
        <TarotCard title="تنظیمات امنیتی" className="lg:col-span-2">
          <form onSubmit={handleSave} className="space-y-4">
            <div className="border-b border-border pb-4 mb-4">
              <div className="font-medium mb-2">تغییر رمز عبور</div>
              <div className="flex items-center gap-2">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  placeholder="رمز عبور فعلی"
                  className="flex-1 rounded-xl border border-[#E2E8F0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#005A9C] focus:ring-2 focus:ring-[#005A9C]/20 disabled:opacity-60"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={loading}
                  className="px-3 py-2 rounded-xl border border-[#E2E8F0] text-sm hover:bg-muted/50 transition"
                  aria-label={showPassword ? "مخفی کردن رمز" : "نمایش رمز"}
                >
                  {showPassword ? <FaEyeSlashIcon className="h-4 w-4" /> : <FaEyeIcon className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div>
              <div className="font-medium mb-2">رمز عبور جدید</div>
              <div className="flex items-center gap-2">
                <input
                  type={showNewPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  disabled={loading}
                  placeholder="حداقل ۸ کاراکتر"
                  className="flex-1 rounded-xl border border-[#E2E8F0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#005A9C] focus:ring-2 focus:ring-[#005A9C]/20 disabled:opacity-60"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  disabled={loading}
                  className="px-3 py-2 rounded-xl border border-[#E2E8F0] text-sm hover:bg-muted/50 transition"
                  aria-label={showNewPassword ? "مخفی کردن رمز" : "نمایش رمز"}
                >
                  {showNewPassword ? <FaEyeSlashIcon className="h-4 w-4" /> : <FaEyeIcon className="h-4 w-4" />}
                </button>
              </div>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
                placeholder="تکرار رمز جدید"
                className="mt-2 w-full rounded-xl border border-[#E2E8F0] bg-white px-3 py-2 text-sm outline-none transition focus:border-[#005A9C] focus:ring-2 focus:ring-[#005A9C]/20 disabled:opacity-60"
              />
              {confirmPasswordError && (
                <p className="text-sm mt-1 text-error">{confirmPasswordError}</p>
              )}
              {saveError && (
                <p className="text-sm mt-1 text-error">{saveError}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-4 w-full justify-center px-4 py-2 bg-secondary text-secondary-foreground rounded-xl hover:bg-secondary/20 transition"
            >
              {loading ? "در حال ذخیره..." : "ذخیره تغییرات"}
            </button>
          </form>
        </TarotCard>
      </div>
    </DashboardShell>
  );
}
