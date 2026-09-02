"use client";

import { NewDashboardShell } from "@/components/layout/NewDashboardShell";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useState, useEffect } from "react";
import { apiClient, getApiErrorMessage } from "@/lib/api";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";
import { useUXStore } from "@/store/useUXStore";
import { cn } from "@/lib/cn";

export default function SettingsPage() {
  const addToast = useUXStore((state) => state.addToast);
  const [selectedCountry, setSelectedCountry] = useState("ir");
  const [selectedIndex, setSelectedIndex] = useState("tepix");
  const [selectedStock, setSelectedStock] = useState("");
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    sms: false,
    telegram: true
  });
  const [marketData, setMarketData] = useState<any>(null);
  const [countries, setCountries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function loadInitialData() {
      setLoading(true);
      try {
        const [prefsRes, countriesRes] = await Promise.all([
          apiClient.get("settings/market-preferences"),
          apiClient.get("settings/countries")
        ]);
        
        if (active) {
          if (prefsRes.data) setMarketData(prefsRes.data);
          if (countriesRes.data) setCountries(countriesRes.data);
        }
      } catch (error) {
        console.error("Failed to load settings data", error);
      } finally {
        if (active) setLoading(false);
      }
    }
    loadInitialData();
    return () => { active = false; };
  }, []);

  const data = marketData ? marketData[selectedCountry] : null;
  const countryInfo = countries.find(c => c.id === selectedCountry);

  const toggleNotification = (type: keyof typeof notifications) => {
    setNotifications(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await apiClient.post("settings/market-preferences", {
        ...marketData,
        [selectedCountry]: {
          ...data,
          index: selectedIndex,
          stock: selectedStock,
          industry: selectedIndustry },
        notifications,
      });
      const [prefsRes] = await Promise.all([
        apiClient.get("settings/market-preferences"),
      ]);
      if (prefsRes.data) setMarketData(prefsRes.data);
      addToast({ type: "success", message: "Settings saved successfully" });
    } catch (error) {
      addToast({ type: "error", message: getApiErrorMessage(error) });
    } finally {
      setLoading(false);
    }
  };

  const notificationTypes = [
    { id: "email", label: "Email", icon: "📧" },
    { id: "push", label: "Push Notifications", icon: "Alerts" },
    { id: "sms", label: "SMS", icon: "📱" },
    { id: "telegram", label: "Telegram", icon: "✈️" }
  ];

  if (loading && !marketData) {
    return (
      <NewDashboardShell title={t("app.settings.title", "en")}>
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          {t("app.settings.loading", "en")}
        </div>
      </NewDashboardShell>
    );
  }

  return (
    <NewDashboardShell title={t("app.settings.title", "en")}>
      <div className="flex flex-col gap-6">
        <Card icon="Settings" title={t("app.settings.overview_title", "en")}>
          <p className="text-muted-foreground text-justify">
            {t("app.settings.overview_desc", "en")}
          </p>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-3">
            <Card icon="[Global]" title={t("app.settings.country_selection", "en")}>
              <div className="space-y-2">
                {countries.map((country) => {
                  const isSelected = selectedCountry === country.id;
                  return (
                    <button
                      key={country.id}
                      onClick={() => setSelectedCountry(country.id)}
                      className={cn(
                        "w-full p-3 rounded-lg border transition-all flex items-center gap-2",
                        isSelected 
                          ? "border-primary bg-primary-light" 
                          : "border-border hover:border-border"
                      )}
                    >
                      <span className="text-2xl">{country.flag}</span>
                      <div className={false ? "text-right" : "text-left"}>
                        <div className="font-medium text-sm">{country.name}</div>
                        <div className="text-xs text-muted-foreground">{country.region}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </Card>
          </div>

          <div className="lg:col-span-9">
            <Card 
              icon={countryInfo?.flag || "🏳️"} 
              title={t("app.settings.market_config", "en").replace("{country}", countryInfo?.name || "")}
            >
              {data ? (
                <div className="space-y-6">
                  <div>
                    <h4 className="font-bold mb-3 text-sm flex items-center gap-2">
                      <span>[Chart]</span> {t("app.settings.indices", "en")}
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {data.indices?.map((index: any) => (
                        <label
                          key={index.id}
                          className={cn(
                            "flex items-center gap-2 p-3 rounded-xl border cursor-pointer transition-all",
                            selectedIndex === index.id 
                              ? "border-primary bg-primary-light" 
                              : "border-border hover:border-border"
                          )}
                        >
                          <input
                            type="radio"
                            name="index"
                            checked={selectedIndex === index.id}
                            onChange={() => setSelectedIndex(index.id)}
                            className="text-primary focus:ring-primary"
                          />
                          <div className={false ? "text-right" : "text-left"}>
                            <div className="font-medium text-sm">{index.name}</div>
                            <div className="text-xs text-muted-foreground">{index.desc}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {data.stocks?.length > 0 && (
                    <div>
                      <h4 className="font-bold mb-3 text-sm flex items-center gap-2">
                        <span>📈</span> {t("app.settings.stocks", "en")}
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                        {data.stocks.map((stock: any) => (
                          <label
                            key={stock.id}
                            className={cn(
                              "flex items-center gap-2 p-3 rounded-xl border cursor-pointer transition-all",
                              selectedStock === stock.id 
                                ? "border-primary bg-primary-light" 
                                : "border-border hover:border-border"
                            )}
                          >
                            <input
                              type="radio"
                              name="stock"
                              checked={selectedStock === stock.id}
                              onChange={() => setSelectedStock(stock.id)}
                              className="text-primary focus:ring-primary"
                            />
                            <div className={false ? "text-right" : "text-left"}>
                              <div className="font-medium text-sm">{stock.name}</div>
                              <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {data.industries?.length > 0 && (
                    <div>
                      <h4 className="font-bold mb-3 text-sm flex items-center gap-2">
                        <span>🏭</span> {t("app.settings.industries", "en")}
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {data.industries.map((industry: any) => (
                          <label
                            key={industry.id}
                            className={cn(
                              "flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all",
                              selectedIndustry === industry.id 
                                ? "border-primary bg-primary-light" 
                                : "border-border hover:border-border"
                            )}
                          >
                            <div className="flex items-center gap-2">
                              <input
                                type="radio"
                                name="industry"
                                checked={selectedIndustry === industry.id}
                                onChange={() => setSelectedIndustry(industry.id)}
                                className="text-primary focus:ring-primary"
                              />
                              <span className="font-medium text-sm">{industry.name}</span>
                            </div>
                            <span className={cn(
                              "text-xs font-bold",
                              industry.change?.startsWith("+") ? "text-success" : "text-error"
                            )}>
                              {industry.change}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="pt-4 border-t border-border/60">
                    <h4 className="font-bold mb-3 text-sm flex items-center gap-2">
                      <span>Alerts</span> {t("app.settings.notification_prefs", "en")}
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {notificationTypes.map((type) => (
                        <label
                          key={type.id}
                          className="flex items-center justify-between p-3 rounded-xl bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-xl">{type.icon}</span>
                            <span className="font-medium text-sm">{type.label}</span>
                          </div>
                          <div className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={notifications[type.id as keyof typeof notifications]}
                              onChange={() => toggleNotification(type.id as keyof typeof notifications)}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-surface after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="flex justify-end gap-3 pt-6">
                    <Button onClick={handleSave} className="px-8">
                      {t("app.settings.save_settings", "en")}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="p-12 text-center text-muted-foreground flex flex-col items-center gap-4">
                  <div className="text-4xl">📭</div>
                  <p>{t("app.settings.no_config", "en")}</p>
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </NewDashboardShell>
  );
}
