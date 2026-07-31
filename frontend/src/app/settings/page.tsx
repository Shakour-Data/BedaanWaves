"use client";

import { DashboardShell } from "@/components/layout/DashboardShell";
import { TarotCard } from "@/components/ui/TarotCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useState } from "react";

const countries = [
  { id: "ir", name: "Iran", flag: "🇮🇷", region: "Middle East" },
  { id: "us", name: "USA", flag: "🇺🇸", region: "North America" },
  { id: "eu", name: "Europe", flag: "🇪🇺", region: "Europe" },
  { id: "as", name: "Asia", flag: "🌏", region: "Asia Pacific" },
  { id: "crypto", name: "Cryptocurrency", flag: "₿", region: "Digital" }
];

const marketData = {
  ir: {
    indices: [
      { id: "tepix", name: "TEPIX", desc: "Tehran Stock Exchange Index" },
      { id: "tedpix", name: "TEDPIX", desc: "The Dow Iran" }
    ],
    stocks: [
      { id: "mav", name: "Mave", symbol: "MVE" },
      { id: "dkd", name: "Dekhoon Kala Dar", symbol: "DKD" }
    ],
    industries: [
      { id: "energy", name: "Energy", change: "+2.5%" },
      { id: "tech", name: "Technology", change: "+3.1%" }
    ],
    crypto: [
      { id: "btc", name: "Bitcoin", symbol: "BTC", price: "$45,000", change: "+2%" },
      { id: "eth", name: "Ethereum", symbol: "ETH", price: "$2,800", change: "+1.5%" }
    ]
  },
  us: {
    indices: [
      { id: "spx", name: "S&P 500", desc: "Standard & Poor's 500" },
      { id: "nas", name: "NASDAQ", desc: "NASDAQ Composite" }
    ],
    stocks: [
      { id: "aapl", name: "Apple", symbol: "AAPL" },
      { id: "msft", name: "Microsoft", symbol: "MSFT" }
    ],
    industries: [
      { id: "tech", name: "Technology", change: "+4.2%" },
      { id: "health", name: "Healthcare", change: "+1.8%" }
    ],
    crypto: [
      { id: "btc", name: "Bitcoin", symbol: "BTC", price: "$45,000", change: "+2%" },
      { id: "eth", name: "Ethereum", symbol: "ETH", price: "$2,800", change: "+2.1%" }
    ]
  },
  eu: {
    indices: [
      { id: "ftse", name: "FTSE 100", desc: "Financial Times Stock Exchange 100" },
      { id: "dax", name: "DAX", desc: "Germany's DAX Index" }
    ],
    stocks: [
      { id: "sap", name: "SAP", symbol: "SAP" },
      { id: "vow", name: "Volkswagen", symbol: "VOW" }
    ],
    industries: [
      { id: "auto", name: "Automotive", change: "+1.9%" },
      { id: "finance", name: "Financial", change: "+0.8%" }
    ],
    crypto: [
      { id: "btc", name: "Bitcoin", symbol: "BTC", price: "$45,000", change: "+2%" }
    ]
  },
  crypto: {
    indices: [
      { id: "crypto10", name: "Crypto Top 10", desc: "Top 10 Cryptocurrencies" },
      { id: "defi", name: "DeFi Index", desc: "Decentralized Finance Track" }
    ],
    stocks: [],
    industries: [
      { id: "defi", name: "DeFi Protocol", change: "+8.5%" },
      { id: "layer1", name: "Layer 1 Blockchain", change: "+10.2%" }
    ],
    crypto: [
      { id: "sol", name: "Solana", symbol: "SOL", price: "$125", change: "+5.3%" },
      { id: "ada", name: "Cardano", symbol: "ADA", price: "$0.45", change: "+3.4%" },
      { id: "avax", name: "Avalanche", symbol: "AVAX", price: "$75", change: "+6.1%" }
    ]
  }
};

const notificationTypes = [
  { id: "email", label: "Email Notifications", icon: "📧" },
  { id: "push", label: "Push Notifications", icon: "🔔" },
  { id: "sms", label: "SMS Alerts", icon: "📱" },
  { id: "telegram", label: "Telegram Bot", icon: "📨" }
];

export default function SettingsPage() {
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

  const data = marketData[selectedCountry as keyof typeof marketData] || marketData.ir;
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

  const handleSave = () => {
    // Save settings logic
    console.log("Settings saved:", {
      country: selectedCountry,
      index: selectedIndex,
      stock: selectedStock,
      industry: selectedIndustry,
      crypto: selectedCrypto,
      currencies: selectedCurrencies,
      notifications
    });
  };

  return (
    <DashboardShell title="Professional Market Settings">
      <div className="flex flex-col gap-6">
        <TarotCard icon="⚙️" title="Market Preferences Configuration">
          <p className="text-muted-foreground text-justify">
            Configure your personalized market analysis settings. Select countries, indices, stocks, industries, and cryptocurrency preferences. Multiple market selections are supported with dynamic tab organization.
          </p>
        </TarotCard>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Country Selection - Left Sidebar */}
          <div className="lg:col-span-3">
            <TarotCard icon="🌍" title="Country Selection">
              <div className="space-y-2">
                {countries.map((country) => {
                  const isSelected = selectedCountry === country.id;
                  return (
                    <button
                      key={country.id}
                      onClick={() => setSelectedCountry(country.id)}
                      className={`w-full p-3 rounded-lg border transition-all flex items-center gap-2
                        ${isSelected ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" : "border-gray-200 hover:border-gray-300"}
                      `}
                    >
                      <span className="text-2xl">{country.flag}</span>
                      <div className="text-left">
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
              title={`${countryInfo?.name} Market Configuration`}
            >
              <div className="space-y-4">
                {/* Indices Section */}
                <div>
                  <h4 className="font-medium mb-3 text-sm">Indices</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {data.indices.map((index) => (
                      <label
                        key={index.id}
                        className={`flex items-center gap-2 p-3 rounded border cursor-pointer transition-all
                          ${selectedIndex === index.id ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" : "border-gray-200 hover:border-gray-300"}
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
                {data.stocks.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3 text-sm">Stocks</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                      {data.stocks.map((stock) => (
                        <label
                          key={stock.id}
                          className={`flex items-center gap-2 p-3 rounded border cursor-pointer transition-all
                            ${selectedStock === stock.id ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" : "border-gray-200 hover:border-gray-300"}
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
                  <h4 className="font-medium mb-3 text-sm">Industries</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {data.industries.map((industry) => (
                      <label
                        key={industry.id}
                        className={`flex items-center justify-between p-3 rounded border cursor-pointer transition-all
                          ${selectedIndustry === industry.id ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" : "border-gray-200 hover:border-gray-300"}
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
                          industry.change.startsWith("+") ? "text-green-600" : "text-red-600"
                        }`}>
                          {industry.change}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Cryptocurrency Section */}
                <div>
                  <h4 className="font-medium mb-3 text-sm">Cryptocurrencies</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                    {data.crypto.map((coin) => (
                      <label
                        key={coin.id}
                        className={`flex items-center justify-between p-3 rounded border cursor-pointer transition-all
                          ${selectedCrypto === coin.id ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20" : "border-gray-200 hover:border-gray-300"}
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
                          coin.change.startsWith("+") ? "text-green-600" : "text-red-600"
                        }`}>
                          {coin.change}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Currencies Section */}
                <div>
                  <h4 className="font-medium mb-3 text-sm">Trading Currencies</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 gap-2">
                    {["IRR", "USD", "EUR", "GBP", "JPY", "CNY", "BTC", "ETH"].map((currency) => (
                      <label
                        key={currency}
                        className="flex items-center justify-center gap-2 p-2 rounded border cursor-pointer transition-all
                          hover:bg-muted/50
                        "
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
                <TarotCard icon="🔔" title="Notification Preferences">
                  <div className="space-y-2">
                    {notificationTypes.map((type) => (
                      <label
                        key={type.id}
                        className="flex items-center justify-between p-2 rounded-lg bg-muted/30 cursor-pointer"
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
                      </label>
                    ))}
                  </div>
                </TarotCard>

                {/* Save Button */}
                <div className="flex justify-end gap-3 pt-4">
                  <PrimaryButton onClick={handleSave}>
                    Save Settings
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