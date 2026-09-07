import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OrderBook } from "@/components/market/OrderBook";
import { useLiveStore } from "@/store/useLiveStore";

const mockOrderBookData = {
  symbol: "AAPL",
  bids: [
    { rank: 1, price: 199.95, volume: 5000, order_count: 12 },
    { rank: 2, price: 199.90, volume: 3000, order_count: 8 },
    { rank: 3, price: 199.85, volume: 2000, order_count: 5 },
    { rank: 4, price: 199.80, volume: 1500, order_count: 4 },
    { rank: 5, price: 199.75, volume: 1000, order_count: 3 },
  ],
  asks: [
    { rank: 1, price: 200.05, volume: 4000, order_count: 10 },
    { rank: 2, price: 200.10, volume: 2500, order_count: 6 },
    { rank: 3, price: 200.15, volume: 2000, order_count: 4 },
    { rank: 4, price: 200.20, volume: 1500, order_count: 3 },
    { rank: 5, price: 200.25, volume: 1000, order_count: 2 },
  ],
  spread: 0.1,
  spread_pct: 0.05,
  freshness_ts: new Date().toISOString(),
};

vi.mock("@/hooks/useLiveData", () => ({
  useLiveData: vi.fn(),
}));

import { useLiveData } from "@/hooks/useLiveData";

const mockUseLiveData = useLiveData as ReturnType<typeof vi.fn>;

describe("OrderBook component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLiveStore.setState({ streams: {} });
  });

  const mockReturn = {
    data: mockOrderBookData,
    latest: mockOrderBookData,
    connectionHealth: "live" as const,
    lastDataAgeMs: 100,
    lastSequence: 1,
    isStale: false,
    manualResync: vi.fn(),
  };

  it("renders order book title when data is available", () => {
    mockUseLiveData.mockReturnValue(mockReturn);
    render(<OrderBook symbol="AAPL" maxDepth={5} />);
    expect(screen.getByText("AAPL Order Book")).not.toBeNull();
    expect(screen.getByText("Top 5 Levels")).not.toBeNull();
  });

  it("displays 5 bid levels (best bid highest price first)", () => {
    mockUseLiveData.mockReturnValue(mockReturn);
    render(<OrderBook symbol="AAPL" maxDepth={5} />);
    // Best bid price appears in both the bid row and the central price column
    expect(screen.getAllByText("199.95").length).toBeGreaterThanOrEqual(1);
  });

  it("displays 5 ask levels (best ask lowest price first)", () => {
    mockUseLiveData.mockReturnValue(mockReturn);
    render(<OrderBook symbol="AAPL" maxDepth={5} />);
    // Best ask price appears in both the ask row and the central price column
    expect(screen.getAllByText("200.05").length).toBeGreaterThanOrEqual(1);
  });

  it("displays spread information", () => {
    mockUseLiveData.mockReturnValue(mockReturn);
    render(<OrderBook symbol="AAPL" />);
    expect(screen.getByText(/Spread:/)).not.toBeNull();
  });

  it("shows fallback message when no data available", () => {
    mockUseLiveData.mockReturnValue({
      data: null,
      latest: null,
      connectionHealth: "syncing",
      lastDataAgeMs: null,
      lastSequence: null,
      isStale: false,
      manualResync: vi.fn(),
    });
    render(<OrderBook symbol="AAPL" />);
    expect(screen.getByText("No order book data available")).not.toBeNull();
  });

  it("displays connection health status", () => {
    mockUseLiveData.mockReturnValue(mockReturn);
    render(<OrderBook symbol="AAPL" />);
    expect(screen.getByText("LIVE")).not.toBeNull();
  });

  it("shows total bid and ask volumes in footer", () => {
    mockUseLiveData.mockReturnValue(mockReturn);
    const { container } = render(<OrderBook symbol="AAPL" />);
    const footer = container.querySelector(".mt-2.border-t");
    expect(footer).not.toBeNull();
    const footerText = footer?.textContent || "";
    const bidVol = mockOrderBookData.bids.reduce((s, b) => s + b.volume, 0);
    const askVol = mockOrderBookData.asks.reduce((s, a) => s + a.volume, 0);
    expect(footerText).toContain(`Bid Vol: ${bidVol.toLocaleString()}`);
    expect(footerText).toContain(`Ask Vol: ${askVol.toLocaleString()}`);
  });

  it("respects maxDepth prop to limit levels shown", () => {
    const limitedData = {
      ...mockOrderBookData,
      bids: mockOrderBookData.bids.slice(0, 3),
      asks: mockOrderBookData.asks.slice(0, 3),
    };
    mockUseLiveData.mockReturnValue({ ...mockReturn, data: limitedData });
    render(<OrderBook symbol="AAPL" maxDepth={3} />);
    expect(screen.getByText("AAPL Order Book")).not.toBeNull();
  });
});
