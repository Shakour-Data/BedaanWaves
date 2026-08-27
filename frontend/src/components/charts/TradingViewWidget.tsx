"use client";

interface TradingViewWidgetProps {
  symbol?: string;
  theme?: "light" | "dark";
  height?: number;
}

export function TradingViewWidget({
  symbol = "NASDAQ:AAPL",
  theme = "light",
  height = 420 }: TradingViewWidgetProps) {
  return (
    <iframe
      src={`https://s.tradingview.com/widgetembed/?frameElement=true&symbol=${encodeURIComponent(symbol)}&interval=D&timezone=Etc/UTC&theme=${theme}&style=1&locale=en&enable_publishing=false&allow_symbol_change=true&hide_side_toolbar=false&height=${height}`}
      style={{ width: "100%", height }}
      frameBorder="0"
      allowFullScreen
      allow="clipboard-write"
    />
  );
}
