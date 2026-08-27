"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/useAuthStore";
import { cn } from "@/lib/cn";

export default function SettingsPage() {
  const { currentLang } = useAuthStore();
  const [selectedCountry, setSelectedCountry] = useState("ir");
  const [selectedIndex, setSelectedIndex] = useState("tepix");
  const [selectedStock, setSelectedStock] = useState("");
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const [selectedCrypto, setSelectedCrypto] = useState("");
  const [selectedCurrencies, setSelectedCurrencies] = useState(["IRR", "USD"]);
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
          apiClient.get("/settings/market-preferences"),
          apiClient.get("/settings/countries")
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

  const toggleCurrency = (currency: string) => {
    if (selectedCurrencies.includes(currency)) {
      setSelectedCurrencies(selectedCurrencies.filter(c => c !== currency));
    } else {
      setSelectedCurrencies([...selectedCurrencies, currency]);
    }
  };

  const toggleNotification = (type: keyof typeof notifications) => {
    setNotifications(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await apiClient.post("/settings/market-preferences", {
        ...marketData,
        [selectedCountry]: {
          ...data,
          index: selectedIndex,
          stock: selectedStock,
          industry: selectedIndustry,
          crypto: selectedCrypto,
        },
        notifications,
        currencies: selectedCurrencies
      });
    } catch (error) {
      // Handle error (e.g., show toast)
    } finally {
      setLoading(false);
    }
  };

  const notificationTypes = [
    { id: "email", label: currentLang === "fa" ? "ایمیل" : "Email", icon: "📧" },
    { id: "push", label: currentLang === "fa" ? "پوش نوتیفیکیشن" : "Push Notifications", icon: "🔔" },
    { id: "sms", label: currentLang === "fa" ? "پیامک" : "SMS", icon: "📱" },
    { id: "telegram", label: currentLang === "fa" ? "تلگرام" : "Telegram", icon: "✈️" }
  ];

  if (loading && !marketData) {
    return (
      <DashboardShell title={t("app.settings.title", currentLang)}>
        <div className="flex min-h-[40vh] items-center justify-center text-muted-foreground">
          {t("app.settings.loading", currentLang)}
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title={t("app.settings.title", currentLang)}>
      <div className="flex flex-col gap-6">
        <TarotCard icon="⚙️" title={t("app.settings.overview_title", currentLang)}>
          <p className="text-muted-foreground text-justify">
            {t("app.settings.overview_desc", currentLang)}
          </p>
        </TarotCard>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Country Selection - Left Sidebar */}
          <div className="lg:col-span-3">
            <TarotCard icon="🌍" title={t("app.settings.country_selection", currentLang)}>
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
                          ? "border-red-500 bg-red-50 dark:bg-red-900/20" 
                          : "border-gray-200 hover:border-gray-300"
                      )}
                    >
                      <span className="text-2xl">{country.flag}</span>
                      <div className={currentLang === "fa" ? "text-right" : "text-left"}>
                        <div className="font-medium text-sm">{country.name}</div>
                        <div className="text-xs text-muted-foreground">{country.region}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </TarotCard>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-9">
            <TarotCard 
              icon={countryInfo?.flag || "🏳️"} 
              title={t("app.settings.market_config", currentLang).replace("{country}", countryInfo?.name || "")}
            >
              {data ? (
                <div className="space-y-6">
                  {/* Indices Section */}
                  <div>
                    <h4 className="font-bold mb-3 text-sm flex items-center gap-2">
                      <span>📊</span> {t("app.settings.indices", currentLang)}
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {data.indices?.map((index: any) => (
                        <label
                          key={index.id}
                          className={cn(
                            "flex items-center gap-2 p-3 rounded-xl border cursor-pointer transition-all",
                            selectedIndex === index.id 
                              ? "border-red-500 bg-red-50 dark:bg-red-900/20" 
                              : "border-gray-200 hover:border-gray-300"
                          )}
                        >
                          <input
                            type="radio"
                            name="index"
                            checked={selectedIndex === index.id}
                            onChange={() => setSelectedIndex(index.id)}
                            className="text-red-600 focus:ring-red-500"
                          />
                          <div className={currentLang === "fa" ? "text-right" : "text-left"}>
                            <div className="font-medium text-sm">{index.name}</div>
                            <div className="text-xs text-muted-foreground">{index.desc}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Stocks Section */}
                  {data.stocks?.length > 0 && (
                    <div>
                      <h4 className="font-bold mb-3 text-sm flex items-center gap-2">
                        <span>📈</span> {t("app.settings.stocks", currentLang)}
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                        {data.stocks.map((stock: any) => (
                          <label
                            key={stock.id}
                            className={cn(
                              "flex items-center gap-2 p-3 rounded-xl border cursor-pointer transition-all",
                              selectedStock === stock.id 
                                ? "border-red-500 bg-red-50 dark:bg-red-900/20" 
                                : "border-gray-200 hover:border-gray-300"
                            )}
                          >
                            <input
                              type="radio"
                              name="stock"
                              checked={selectedStock === stock.id}
                              onChange={() => setSelectedStock(stock.id)}
                              className="text-red-600 focus:ring-red-500"
                            />
                            <div className={currentLang === "fa" ? "text-right" : "text-left"}>
                              <div className="font-medium text-sm">{stock.name}</div>
                              <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Industries Section */}
                  {data.industries?.length > 0 && (
                    <div>
                      <h4 className="font-bold mb-3 text-sm flex items-center gap-2">
                        <span>🏭</span> {t("app.settings.industries", currentLang)}
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {data.industries.map((industry: any) => (
                          <label
                            key={industry.id}
                            className={cn(
                              "flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all",
                              selectedIndustry === industry.id 
                                ? "border-red-500 bg-red-50 dark:bg-red-900/20" 
                                : "border-gray-200 hover:border-gray-300"
                            )}
                          >
                            <div className="flex items-center gap-2">
                              <input
                                type="radio"
                                name="industry"
                                checked={selectedIndustry === industry.id}
                                onChange={() => setSelectedIndustry(industry.id)}
                                className="text-red-600 focus:ring-red-500"
                              />
                              <span className="font-medium text-sm">{industry.name}</span>
                            </div>
                            <span className={cn(
                              "text-xs font-bold",
                              industry.change?.startsWith("+") ? "text-green-600" : "text-red-600"
                            )}>
                              {industry.change}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Cryptocurrency Section */}
                  {data.crypto?.length > 0 && (
                    <div>
                      <h4 className="font-bold mb-3 text-sm flex items-center gap-2">
                        <span>₿</span> {t("app.settings.cryptocurrencies", currentLang)}
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                        {data.crypto.map((coin: any) => (
                          <label
                            key={coin.id}
                            className={cn(
                              "flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all",
                              selectedCrypto === coin.id 
                                ? "border-red-500 bg-red-50 dark:bg-red-900/20" 
                                : "border-gray-200 hover:border-gray-300"
                            )}
                          >
                            <div className="flex items-center gap-2">
                              <input
                                type="radio"
                                name="crypto"
                                checked={selectedCrypto === coin.id}
                                onChange={() => setSelectedCrypto(coin.id)}
                                className="text-red-600 focus:ring-red-500"
                              />
                              <div className={currentLang === "fa" ? "text-right" : "text-left"}>
                                <div className="font-medium text-sm">{coin.name}</div>
                                <div className="text-xs text-muted-foreground">{coin.symbol} | ${coin.price}</div>
                              </div>
                            </div>
                            <span className={cn(
                              "text-xs font-bold",
                              coin.change?.startsWith("+") ? "text-green-600" : "text-red-600"
                            )}>
                              {coin.change}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Currencies Section */}
                  <div>
                    <h4 className="font-bold mb-3 text-sm flex items-center gap-2">
                      <span>💱</span> {t("app.settings.trading_currencies", currentLang)}
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {["IRR", "USD", "EUR", "GBP", "JPY", "CNY", "BTC", "ETH"].map((currency) => (
                        <label
                          key={currency}
                          className="flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-all hover:bg-muted/50"
                        >
                          <input
                            type="checkbox"
                            checked={selectedCurrencies.includes(currency)}
                            onChange={() => toggleCurrency(currency)}
                            className="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
                          />
                          <span className="font-mono text-sm">{currency}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Notification Settings */}
                  <div className="pt-4 border-t border-border/60">
                    <h4 className="font-bold mb-3 text-sm flex items-center gap-2">
                      <span>🔔</span> {t("app.settings.notification_prefs", currentLang)}
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
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Save Button */}
                  <div className="flex justify-end gap-3 pt-6">
                    <PrimaryButton onClick={handleSave} className="px-8 shadow-lg shadow-red-600/20">
                      {t("app.settings.save_settings", currentLang)}
                    </PrimaryButton>
                  </div>
                </div>
              ) : (
                <div className="p-12 text-center text-muted-foreground flex flex-col items-center gap-4">
                  <div className="text-4xl">📭</div>
                  <p>{t("app.settings.no_config", currentLang)}</p>
                </div>
              )}
            </TarotCard>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
