"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";

const countries = [
  { id: "ir", name: "Iran", flag: "🇮🇷", region: "Middle East" },
  { id: "us", name: "USA", flag: "🇺🇸", region: "North America" },
  { id: "eu", name: "Europe", flag: "🇪🇺", region: "Europe" },
  { id: "as", name: "Asia", flag: "🌏", region: "Asia Pacific" },
  { id: "crypto", name: "Cryptocurrency", flag: "₿", region: "Digital" },
];

const marketData = {
  ir: {
    indices: [
      { id: "tepix", name: "TEPIX", desc: "شاخص کل بورس تهران" },
      { id: "tedpix", name: "TEDPIX", desc: "شاخص کل proportion دارایی‌ها" },
    ],
    stocks: [
      { id: "mav", name: "Mave", symbol: "MVE" },
      { id: "dkd", name: "Dekhoon Kala Dar", symbol: "DKD" },
    ],
    industries: [
      { id: "energy", name: "انرژی", change: "+2.5%" },
      { id: "tech", name: "تکنولوژی", change: "+3.1%" },
    ],
    crypto: [
      { id: "btc", name: "Bitcoin", symbol: "BTC", price: "$45,000", change: "+2%" },
      { id: "eth", name: "Ethereum", symbol: "ETH", price: "$2,800", change: "+1.5%" },
    ],
  },
  us: {
    indices: [
      { id: "spx", name: "S&P 500", desc: "شاخص استاندارد و پور 500" },
      { id: "nas", name: "NASDAQ", desc: "شاخص ترکیبی ناسداک" },
    ],
    stocks: [
      { id: "aapl", name: "Apple", symbol: "AAPL" },
      { id: "msft", name: "Microsoft", symbol: "MSFT" },
    ],
    industries: [
      { id: "tech", name: "تکنولوژی", change: "+4.2%" },
      { id: "health", name: "سلامت", change: "+1.8%" },
    ],
    crypto: [
      { id: "btc", name: "Bitcoin", symbol: "BTC", price: "$45,000", change: "+2%" },
      { id: "eth", name: "Ethereum", symbol: "ETH", price: "$2,800", change: "+2.1%" },
    ],
  },
  eu: {
    indices: [
      { id: "ftse", name: "FTSE 100", desc: "شاخص Financil Times 100" },
      { id: "dax", name: "DAX", desc: "شاخص DAX آلمان" },
    ],
    stocks: [
      { id: "sap", name: "SAP", symbol: "SAP" },
      { id: "vow", name: "Volkswagen", symbol: "VOW" },
    ],
    industries: [
      { id: "auto", name: "خودروسازی", change: "+1.9%" },
      { id: "finance", name: "مالی", change: "+0.8%" },
    ],
    crypto: [
      { id: "btc", name: "Bitcoin", symbol: "BTC", price: "$45,000", change: "+2%" },
    ],
  },
  crypto: {
    indices: [
      { id: "crypto10", name: "Top 10 Crypto", desc: "۱۰ رمزنگار برتر" },
      { id: "defi", name: "DeFi Index", desc: "ردیابی مالی غیرمتمرکز" },
    ],
    stocks: [],
    industries: [
      { id: "defi", name: "پروتکل DeFi", change: "+8.5%" },
      { id: "layer1", name: "بلاکچین لایه ۱", change: "+10.2%" },
    ],
    crypto: [
      { id: "sol", name: "Solana", symbol: "SOL", price: "$125", change: "+5.3%" },
      { id: "ada", name: "Cardano", symbol: "ADA", price: "$0.45", change: "+3.4%" },
      { id: "avax", name: "Avalanche", symbol: "AVAX", price: "$75", change: "+6.1%" },
    ],
  },
  as: {
    indices: [
      { id: "nikkei", name: "Nikkei 225", desc: "شاخص نیکkei 225 ژاپن" },
      { id: "shcomp", name: "SSE Composite", desc: "شاخص ترکیبی شانگهای" },
    ],
    stocks: [
      { id: "tsm", name: "TSMC", symbol: "TSM" },
      { id: "baba", name: "Alibaba", symbol: "BABA" },
    ],
    industries: [
      { id: "semiconductor", name: "نیمه‌هادی", change: "+3.5%" },
      { id: "ecommerce", name: "تجارت الکترونیک", change: "+2.1%" },
    ],
    crypto: [
      { id: "btc", name: "Bitcoin", symbol: "BTC", price: "$45,000", change: "+2%" },
    ],
  },
};

const notificationTypes = [
  { id: "email", label: "اعلان‌های ایمیل", icon: "📧" },
  { id: "push", label: "اعلان‌های Push", icon: "🔔" },
  { id: "sms", label: "هشدارهای SMS", icon: "📱" },
  { id: "telegram", label: "ربات تلگرام", icon: "✈️" },
];

export default function SettingsPage() {
  const [selectedCountry, setSelectedCountry] = useState("us");
  const [selectedIndex, setSelectedIndex] = useState("spx");
  const [selectedStock, setSelectedStock] = useState("");
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const [selectedCrypto, setSelectedCrypto] = useState("");
  const [selectedCurrencies, setSelectedCurrencies] = useState(["USD", "EUR"]);
  const [notifications, setNotifications] = useState({
    email: true,
    push: true,
    sms: false,
    telegram: false,
  });
  const [apiSettingsData, setApiSettingsData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let active = true;
    async function loadSettings() {
      setLoading(true);
      try {
        const res = await apiClient.get("/users/preferences");
        if (active && res.data) {
          setApiSettingsData(res.data);
          if (res.data.country) setSelectedCountry(res.data.country);
          if (res.data.index) setSelectedIndex(res.data.index);
          if (res.data.stock) setSelectedStock(res.data.stock);
          if (res.data.industry) setSelectedIndustry(res.data.industry);
          if (res.data.crypto) setSelectedCrypto(res.data.crypto);
          if (res.data.currencies) setSelectedCurrencies(res.data.currencies);
          if (res.data.notifications) setNotifications(res.data.notifications);
        }
      } catch {
        // Settings will use local defaults if API is unavailable
      } finally {
        if (active) setLoading(false);
      }
    }
    loadSettings();
    return () => { active = false; };
  }, []);

  const data = apiSettingsData?.[selectedCountry as keyof typeof apiSettingsData] || marketData[selectedCountry as keyof typeof marketData];
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
    setSaved(false);
    try {
      await apiClient.post("/users/preferences", {
        country: selectedCountry,
        index: selectedIndex,
        stock: selectedStock,
        industry: selectedIndustry,
        crypto: selectedCrypto,
        currencies: selectedCurrencies,
        notifications
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardShell title="تنظیمات">
      <div className="flex flex-col gap-6">
        <TarotCard title="پیکربندی تنظیمات بازار">
          <p className="text-muted-foreground text-justify">
            تنظیمات تحلیل بازار شخصی‌سازی شده خود را پیکربندی کنید. کشورها، شاخص‌ها، سهام، صنایع و ارزهای دیجیتال را انتخاب کنید.
          </p>
        </TarotCard>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Country Selection - Left Sidebar */}
          <div className="lg:col-span-3">
            <TarotCard title="انتخاب کشور">
              <div className="space-y-2">
                {countries.map((country) => {
                  const isSelected = selectedCountry === country.id;
                  return (
                    <button
                      key={country.id}
                      onClick={() => setSelectedCountry(country.id)}
                      className={`w-full p-3 rounded-lg border transition-all flex items-center gap-2 text-right
                        ${isSelected ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"}
                      `}
                    >
                      <span className="text-2xl">{country.flag}</span>
                      <div>
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
              icon={countryInfo?.flag}
              title={`پیکربندی بازار ${countryInfo?.name}`}
            >
              <div className="space-y-6">
                {/* Indices Section */}
                <div>
                  <h4 className="font-medium mb-3 text-sm">شاخص‌ها</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {data?.indices?.map((index: any) => (
                      <label
                        key={index.id}
                        className={`flex items-center gap-2 p-3 rounded border cursor-pointer transition-all
                          ${selectedIndex === index.id ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"}
                        `}
                      >
                        <input
                          type="radio"
                          name="index"
                          checked={selectedIndex === index.id}
                          onChange={() => setSelectedIndex(index.id)}
                          className="text-blue-500 focus:ring-blue-500"
                        />
                        <div>
                          <div className="font-medium text-sm">{index.name}</div>
                          <div className="text-xs text-muted-foreground">{index.desc}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Stocks Section */}
                {data?.stocks?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 text-sm">سهام</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                      {data.stocks.map((stock: any) => (
                        <label
                          key={stock.id}
                          className={`flex items-center gap-2 p-3 rounded border cursor-pointer transition-all
                            ${selectedStock === stock.id ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"}
                          `}
                        >
                          <input
                            type="radio"
                            name="stock"
                            checked={selectedStock === stock.id}
                            onChange={() => setSelectedStock(stock.id)}
                            className="text-blue-500 focus:ring-blue-500"
                          />
                          <div>
                            <div className="font-medium text-sm">{stock.name}</div>
                            <div className="text-xs text-muted-foreground">{stock.symbol}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {/* Industries Section */}
                <div>
                  <h4 className="font-medium mb-3 text-sm">صنایع</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {data?.industries?.map((industry: any) => (
                      <label
                        key={industry.id}
                        className={`flex items-center justify-between p-3 rounded border cursor-pointer transition-all
                          ${selectedIndustry === industry.id ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"}
                        `}
                      >
                        <div className="flex items-center gap-2">
                          <input
                            type="radio"
                            name="industry"
                            checked={selectedIndustry === industry.id}
                            onChange={() => setSelectedIndustry(industry.id)}
                            className="text-blue-500 focus:ring-blue-500"
                          />
                          <span className="font-medium text-sm">{industry.name}</span>
                        </div>
                        <span className={`text-xs font-medium ${
                          industry.change.startsWith("+") ? "text-success" : "text-error"
                        }`}>
                          {industry.change}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Cryptocurrency Section */}
                {data?.crypto?.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 text-sm">رمززنگاری</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                      {data.crypto.map((coin: any) => (
                        <label
                          key={coin.id}
                          className={`flex items-center justify-between p-3 rounded border cursor-pointer transition-all
                            ${selectedCrypto === coin.id ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"}
                          `}
                        >
                          <div className="flex items-center gap-2">
                            <input
                              type="radio"
                              name="crypto"
                              checked={selectedCrypto === coin.id}
                              onChange={() => setSelectedCrypto(coin.id)}
                              className="text-blue-500 focus:ring-blue-500"
                            />
                            <div>
                              <div className="font-medium text-sm">{coin.name}</div>
                              <div className="text-xs text-muted-foreground">{coin.symbol} | ${coin.price}</div>
                            </div>
                          </div>
                          <span className={`text-xs font-medium ${
                            coin.change.startsWith("+") ? "text-success" : "text-error"
                          }`}>
                            {coin.change}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {/* Currencies Section */}
                <div>
                  <h4 className="font-medium mb-3 text-sm">ارزهای معاملاتی</h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {["USD", "EUR", "GBP", "JPY", "CNY", "CHF", "CAD", "AUD"].map((currency) => (
                      <label
                        key={currency}
                        className="flex items-center justify-center gap-2 p-2 rounded border cursor-pointer transition-all
                          hover:bg-muted/50"
                      >
                        <input
                          type="checkbox"
                          checked={selectedCurrencies.includes(currency)}
                          onChange={() => toggleCurrency(currency)}
                          className="h-4 w-4 rounded border-gray-300 text-blue-500 focus:ring-blue-500"
                        />
                        <span className="font-mono text-sm">{currency}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Notification Settings */}
                <TarotCard title="ترجیحات اعلان">
                  <div className="space-y-2">
                    {notificationTypes.map((type) => (
                      <div
                        key={type.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-muted/30"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-xl">{type.icon}</span>
                          <span className="font-medium text-sm">{type.label}</span>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={notifications[type.id as keyof typeof notifications]}
                            onChange={() => toggleNotification(type.id as keyof typeof notifications)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                    ))}
                  </div>
                </TarotCard>

                {/* Save Button */}
                <div className="flex justify-end gap-3 pt-4">
                  <PrimaryButton onClick={handleSave} disabled={loading}>
                    {saved ? "ذخیره شد!" : loading ? "در حال ذخیره..." : "ذخیره تنظیمات"}
                  </PrimaryButton>
                </div>
              </div>
            </TarotCard>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
