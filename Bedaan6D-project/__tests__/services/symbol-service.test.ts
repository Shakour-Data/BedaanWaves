import { describe, it, expect, beforeEach, vi, Mock } from 'vitest';
import { SymbolService } from '../../src/services/symbol-service';
import { prisma } from '../../src/lib/prisma';

// Type for mock functions
type MockPrismaFunction = Mock & {
  mockResolvedValue: (value: unknown) => void;
  mockRejectedValue: (error: Error) => void;
};

// Mock Prisma client
vi.mock('../../src/lib/prisma', () => ({
  prisma: {
    symbol: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      count: vi.fn(),
    },
    marketData: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
  },
}));

describe('SymbolService', () => {
  let symbolService: SymbolService;

  beforeEach(() => {
    symbolService = new SymbolService();
    vi.clearAllMocks();
  });

  describe('getSymbols', () => {
    it('should return symbols with market data', async () => {
      const mockSymbols = [
        {
          id: 'sym-1',
          isin: 'IRO1FOLD0001',
          symbol: 'فولاد',
          name: 'فولاد مبارکه اصفهان',
          market: 'بورس',
          sector: 'فلزات اساسی',
          subSector: 'فولاد',
          marketData: [
            {
              id: 'md-1',
              date: new Date('2024-01-01'),
              price: 15000,
              rsi: 55.5,
              macd: 2.5,
              peg: 1.2,
              roe: 18.5,
            },
          ],
        },
      ];

      (prisma.symbol.findMany as MockPrismaFunction).mockResolvedValue(mockSymbols);

      const result = await symbolService.getSymbols();

      expect(result).toEqual(mockSymbols);
      expect(prisma.symbol.findMany).toHaveBeenCalledWith({
        include: {
          marketData: {
            orderBy: { date: 'desc' },
            take: 30,
          },
        },
        orderBy: { symbol: 'asc' },
      });
    });

    it('should apply filters correctly', async () => {
      const filters = {
        market: 'بورس',
        sector: 'فلزات اساسی',
        search: 'فولاد',
        limit: 10,
        offset: 0,
      };

      (prisma.symbol.findMany as MockPrismaFunction).mockResolvedValue([]);

      await symbolService.getSymbols(filters);

      expect(prisma.symbol.findMany).toHaveBeenCalledWith({
        where: {
          market: 'بورس',
          sector: 'فلزات اساسی',
          OR: [
            { symbol: { contains: 'فولاد', mode: 'insensitive' } },
            { name: { contains: 'فولاد', mode: 'insensitive' } },
          ],
        },
        include: {
          marketData: {
            orderBy: { date: 'desc' },
            take: 30,
          },
        },
        orderBy: { symbol: 'asc' },
        take: 10,
        skip: 0,
      });
    });

    it('should handle empty filters', async () => {
      (prisma.symbol.findMany as MockPrismaFunction).mockResolvedValue([]);

      await symbolService.getSymbols({});

      expect(prisma.symbol.findMany).toHaveBeenCalledWith({
        where: {},
        include: {
          marketData: {
            orderBy: { date: 'desc' },
            take: 30,
          },
        },
        orderBy: { symbol: 'asc' },
      });
    });
  });

  describe('getSymbol', () => {
    it('should return symbol by id with market data', async () => {
      const mockSymbol = {
        id: 'sym-1',
        isin: 'IRO1FOLD0001',
        symbol: 'فولاد',
        name: 'فولاد مبارکه اصفهان',
        market: 'بورس',
        sector: 'فلزات اساسی',
        subSector: 'فولاد',
        marketData: [
          {
            id: 'md-1',
            date: new Date('2024-01-01'),
            price: 15000,
            rsi: 55.5,
            macd: 2.5,
          },
        ],
      };

      (prisma.symbol.findUnique as MockPrismaFunction).mockResolvedValue(mockSymbol);

      const result = await symbolService.getSymbol('sym-1');

      expect(result).toEqual(mockSymbol);
      expect(prisma.symbol.findUnique).toHaveBeenCalledWith({
        where: { id: 'sym-1' },
        include: {
          marketData: {
            orderBy: { date: 'desc' },
            take: 30,
          },
        },
      });
    });

    it('should return null for non-existent symbol', async () => {
      (prisma.symbol.findUnique as MockPrismaFunction).mockResolvedValue(null);

      const result = await symbolService.getSymbol('non-existent');

      expect(result).toBeNull();
    });
  });

  describe('createSymbol', () => {
    it('should create a new symbol', async () => {
      const symbolData = {
        isin: 'IRO1FOLD0001',
        symbol: 'فولاد',
        name: 'فولاد مبارکه اصفهان',
        market: 'بورس',
        sector: 'فلزات اساسی',
        subSector: 'فولاد',
      };

      const mockCreated = {
        id: 'sym-1',
        ...symbolData,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      (prisma.symbol.create as MockPrismaFunction).mockResolvedValue(mockCreated);

      const result = await symbolService.createSymbol(symbolData);

      expect(result).toEqual(mockCreated);
      expect(prisma.symbol.create).toHaveBeenCalledWith({
        data: symbolData,
      });
    });

    it('should validate required fields', async () => {
      const invalidData = {
        isin: '',
        symbol: '',
        name: '',
        market: '',
        sector: '',
      };

      await expect(symbolService.createSymbol(invalidData))
        .rejects
        .toThrow();
    });
  });

  describe('updateSymbol', () => {
    it('should update symbol', async () => {
      const updateData = {
        name: 'فولاد مبارکه اصفهان (به‌روز شده)',
        sector: 'فلزات اساسی و معادن',
      };

      const mockUpdated = {
        id: 'sym-1',
        isin: 'IRO1FOLD0001',
        symbol: 'فولاد',
        name: 'فولاد مبارکه اصفهان (به‌روز شده)',
        market: 'بورس',
        sector: 'فلزات اساسی و معادن',
        subSector: 'فولاد',
      };

      (prisma.symbol.update as MockPrismaFunction).mockResolvedValue(mockUpdated);

      const result = await symbolService.updateSymbol('sym-1', updateData);

      expect(result).toEqual(mockUpdated);
      expect(prisma.symbol.update).toHaveBeenCalledWith({
        where: { id: 'sym-1' },
        data: updateData,
      });
    });
  });

  describe('deleteSymbol', () => {
    it('should delete symbol', async () => {
      const mockDeleted = {
        id: 'sym-1',
        isin: 'IRO1FOLD0001',
        symbol: 'فولاد',
        name: 'فولاد مبارکه اصفهان',
        market: 'بورس',
        sector: 'فلزات اساسی',
      };

      (prisma.symbol.delete as MockPrismaFunction).mockResolvedValue(mockDeleted);

      const result = await symbolService.deleteSymbol('sym-1');

      expect(result).toEqual(mockDeleted);
      expect(prisma.symbol.delete).toHaveBeenCalledWith({
        where: { id: 'sym-1' },
      });
    });
  });

  describe('addMarketData', () => {
    it('should add market data for symbol', async () => {
      const marketData = {
        date: new Date('2024-01-01'),
        price: 15000,
        rsi: 55.5,
        macd: 2.5,
        peg: 1.2,
        roe: 18.5,
      };

      const mockCreated = {
        id: 'md-1',
        symbolId: 'sym-1',
        ...marketData,
      };

      (prisma.marketData.create as MockPrismaFunction).mockResolvedValue(mockCreated);

      const result = await symbolService.addMarketData('sym-1', marketData);

      expect(result).toEqual(mockCreated);
      expect(prisma.marketData.create).toHaveBeenCalledWith({
        data: {
          ...marketData,
          symbolId: 'sym-1',
        },
      });
    });
  });

  describe('getSymbolCount', () => {
    it('should return count of symbols', async () => {
      (prisma.symbol.count as MockPrismaFunction).mockResolvedValue(42);

      const result = await symbolService.getSymbolCount();

      expect(result).toBe(42);
      expect(prisma.symbol.count).toHaveBeenCalledWith();
    });

    it('should return count with filters', async () => {
      const filters = {
        market: 'بورس',
        sector: 'فلزات اساسی',
      };

      (prisma.symbol.count as MockPrismaFunction).mockResolvedValue(10);

      const result = await symbolService.getSymbolCount(filters);

      expect(result).toBe(10);
      expect(prisma.symbol.count).toHaveBeenCalledWith({
        where: {
          market: 'بورس',
          sector: 'فلزات اساسی',
        },
      });
    });
  });
});