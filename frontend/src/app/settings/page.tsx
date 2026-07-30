"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { useAppStore } from "@/store/useAppStore";
import { useAuthStore } from "@/store/useAuthStore";

const themeColors = [
  { id: "light", label: "روشن", icon: "☀️", primary: "#c62828", secondary: "#1565c0" },
  { id: "dark", label: "تاریک", icon: "🌙", primary: "#ef5350", secondary: "#4caf50" },
];

const languages = [
  { id: "fa", label: "فارسی" },
  { id: "en", label: "English" },
];

const notificationSettings = [
  { id: "email", label: "ایمیل", enabled: true },
  { id: "push", label: "اعلان", enabled: true },
  { id: "sms", label: "اس‌ام‌اس", enabled: false },
  { id: "telegram", label: "تلگرام", enabled: true },
];

const preferenceStats = [
  { label: "تغییرات تم", value: "۱۲ بار", changePct: 3 },
  { label: "زبان‌های استفاده‌شده", value: "۲", changePct: 0 },
  { label: "روش‌های اعلان", value: "۳ فعال", changePct: 2 },
  { label: "زمان آخرین به‌روزرسانی", value: "۵ دقیقه پیش", changePct: 0 },
];

export default function SettingsPage() {
  const { theme, setTheme } = useAppStore();
  const { user } = useAuthStore();

  return (
    <DashboardShell title="تنظیمات">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* User Profile */}
        <TarotCard icon="👤" title="پروفایل کاربر" className="lg:col-span-3">
          <div className="flex items-start gap-4">
            <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center text-2xl">
              👤
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold">{user?.name || "کاربر نمایشی"}</h3>
              <p className="text-sm text-muted-foreground">{user?.email || "user@example.com"}</p>
              <div className="mt-2 flex gap-2">
                <span className="px-2 py-1 rounded text-xs bg-secondary text-secondary-foreground">عضو از: ۱۴۰۲/۰۱/۰۱</span>
                <span className="px-2 py-1 rounded text-xs bg-success/20 text-success">فعال</span>
              </div>
            </div>
          </div>
        </TarotCard>

        {/* Theme Settings */}
        <TarotCard icon="🎨" title="تنظیمات ظاهری" className="lg:col-span-2">
          <div className="space-y-4">
            <div>
              <div className="text-sm font-medium mb-3">تم:</div>
              <div className="grid grid-cols-2 gap-3">
                {themeColors.map((color) => (
                  <button
                    key={color.id}
                    onClick={() => setTheme(color.id as "light" | "dark")}
                    className={`p-4 rounded-lg border-2 transition-all ${theme === color.id
                        ? "border-secondary bg-secondary/10"
                        : "border-border hover:border-muted-foreground"
                      }`}
                  >
                    <div className="text-2xl mb-2">{color.icon}</div>
                    <div className="text-sm font-medium">{color.label}</div>
                    <div className="text-xs text-muted-foreground mt-1">رنگ اصلی: {color.primary}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="text-sm font-medium mb-2">زبان:</div>
              <div className="flex gap-2">
                {languages.map((lang) => (
                  <button
                    key={lang.id}
                    className="px-4 py-2 rounded-lg border border-border hover:bg-muted/50 transition-colors"
                  >
                    {lang.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </TarotCard>

        {/* Notification Settings */}
        <TarotCard icon="🔔" title="تنظیمات اعلان‌ها">
          <div className="space-y-4">
            {notificationSettings.map((setting) => (
              <div key={setting.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <div className="flex items-center gap-3">
                  <span className="text-xl">
                    {setting.id === "email" ? "📧" : setting.id === "push" ? "🔔" : setting.id === "sms" ? "📱" : "📨"}
                  </span>
                  <span className="font-medium">{setting.label}</span>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    defaultChecked={setting.enabled}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-secondary"></div>
                </label>
              </div>
            ))}
          </div>
        </TarotCard>

        {/* Quick Actions */}
        <TarotCard icon="⚡" title="عملیات سریع" className="lg:col-span-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "🔄 به‌روزرسانی پروفایل", icon: "↻" },
              { label: "🔒 تغییر رمز عبور", icon: "🔑" },
              { label: "📧 بازیابی اعلان‌ها", icon: "📤" },
              { label: "🗑️ پاک کردن داده‌های موقت", icon: "🗑️" },
              { label: "📊 گزارش امنیت", icon: "📈" },
              { label: "🏷️ مدیریت لاگ‌ها", icon: "🏷️" },
              { label: "🔧 بازیابی پیش‌فرض‌ها", icon: "🔧" },
              { label: "💾 ذخیره تنظیمات", icon: "💾" },
            ].map((action, i) => (
              <button
                key={i}
                className="p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors text-center"
              >
                <div className="text-xl mb-1">{action.icon}</div>
                <div className="text-xs font-medium">{action.label}</div>
              </button>
            ))}
          </div>
        </TarotCard>

        {/* System Info */}
        <TarotCard icon="🖥️" title="اطلاعات سیستم" className="lg:col-span-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {preferenceStats.map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-xs text-muted-foreground">{stat.label}</div>
                <div className="text-sm font-bold mt-1">{stat.value}</div>
                {stat.changePct !== undefined && (
                  <div className={`text-xs mt-1 ${stat.changePct >= 0 ? "text-success" : "text-primary"}`">
                    {stat.changePct >= 0 ? "↗" : "↘"} {Math.abs(stat.changePct)}%
                  </div>
                )}
              </div>
            ))}
          </div>
        </TarotCard>
      </div>
    </DashboardShell>
  );
}