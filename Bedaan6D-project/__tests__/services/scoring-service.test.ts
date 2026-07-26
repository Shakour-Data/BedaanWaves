import { describe, it, expect, beforeEach, vi, Mock } from 'vitest';
import { ScoringService } from '../../src/services/scoring-service';
import { prisma } from '../../src/lib/prisma';

// Type for mock functions
type MockPrismaFunction = Mock & {
  mockResolvedValue: (value: unknown) => void;
  mockRejectedValue: (error: Error) => void;
};

// Mock Prisma client
vi.mock('../../src/lib/prisma', () => ({
  prisma: {
    score: {
      findMany: vi.fn(),
      findFirst: vi.fn(),
      create: vi.fn(),
      createMany: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      aggregate: vi.fn(),
    },
    symbol: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
    },
    mainDimension: {
      findMany: vi.fn(),
    },
    subDimension: {
      findMany: vi.fn(),
    },
    aspect: {
      findMany: vi.fn(),
    },
    subCategory: {
      findMany: vi.fn(),
    },
    $transaction: vi.fn((operations) => Promise.all(operations)),
  },
}));

describe('ScoringService', () => {
  let scoringService: ScoringService;

  beforeEach(() => {
    scoringService = new ScoringService();
    vi.clearAllMocks();
  });

  describe('calculateScores', () => {
    it('should calculate scores for a symbol', async () => {
      // Mock data
      const mockSymbol = {
        id: 'sym-1',
        isin: 'IRO1FOLD0001',
        symbol: 'فولاد',
        name: 'فولاد مبارکه اصفهان',
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
      };

      const mockHierarchy = [
        {
          id: 'dim-1',
          code: 'TD-01',
          name: 'تحلیل تکنیکال',
          weight: 1.0,
          order: 1,
          subDimensions: [
            {
              id: 'sub-1',
              code: 'TD-01-01',
              name: 'شاخص‌های روند',
              weight: 1.0,
              order: 1,
              aspects: [
                {
                  id: 'asp-1',
                  code: 'TD-01-01-01',
                  name: 'میانگین متحرک',
                  weight: 1.0,
                  order: 1,
                  subCategories: [
                    {
                      id: 'cat-1',
                      code: 'TD-01-01-01-01',
                      name: 'MA-20',
                      weight: 1.0,
                      order: 1,
                    },
                  ],
                },
              ],
            },
          ],
        },
      ];

      // Mock Prisma calls
      (prisma.symbol.findUnique as MockPrismaFunction).mockResolvedValue(mockSymbol);
      (prisma.mainDimension.findMany as MockPrismaFunction).mockResolvedValue(mockHierarchy);
      (prisma.score.createMany as MockPrismaFunction).mockResolvedValue({ count: 5 });

      // Execute
      const result = await scoringService.calculateScores({
        symbolId: 'sym-1',
        date: new Date('2024-01-01'),
      });

      // Assert
      expect(result).toHaveProperty('symbolId', 'sym-1');
      expect(result).toHaveProperty('calculationDate');
      expect(result).toHaveProperty('dimensionScores');
      expect(prisma.symbol.findUnique).toHaveBeenCalledWith({
        where: { id: 'sym-1' },
        include: {
          marketData: {
            where: {
              date: {
                lte: expect.any(Date),
              },
            },
            orderBy: { date: 'desc' },
            take: 30,
          },
        },
      });
      expect(prisma.mainDimension.findMany).toHaveBeenCalledWith({
        include: {
          subDimensions: {
            include: {
              aspects: {
                include: {
                  subCategories: true,
                },
              },
            },
          },
        },
        orderBy: { order: 'asc' },
      });
    });

    it('should handle missing market data', async () => {
      const mockSymbol = {
        id: 'sym-1',
        marketData: [],
      };

      (prisma.symbol.findUnique as MockPrismaFunction).mockResolvedValue(mockSymbol);
      (prisma.mainDimension.findMany as MockPrismaFunction).mockResolvedValue([]);

      await expect(scoringService.calculateScores({
        symbolId: 'sym-1',
        date: new Date('2024-01-01'),
      })).rejects.toThrow('داده‌های بازار برای نماد یافت نشد');
    });

    it('should handle missing hierarchy', async () => {
      const mockSymbol = {
        id: 'sym-1',
        marketData: [{ id: 'md-1', date: new Date('2024-01-01'), price: 15000 }],
      };

      (prisma.symbol.findUnique as MockPrismaFunction).mockResolvedValue(mockSymbol);
      (prisma.mainDimension.findMany as MockPrismaFunction).mockResolvedValue([]);

      await expect(scoringService.calculateScores({
        symbolId: 'sym-1',
        date: new Date('2024-01-01'),
      })).rejects.toThrow('ساختار سلسله‌مراتبی یافت نشد');
    });
  });

  describe('getSymbolScores', () => {
    it('should return scores for a symbol', async () => {
      const mockScores = [
        {
          id: 'score-1',
          value: 85.5,
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
          mainDimension: {
            id: 'dim-1',
            code: 'TD-01',
            name: 'تحلیل تکنیکال',
            weight: 1.0,
          },
        },
      ];

      (prisma.score.findMany as MockPrismaFunction).mockResolvedValue(mockScores);

      const result = await scoringService.getSymbolScores('sym-1');

      expect(result).toEqual(mockScores);
      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: { symbolId: 'sym-1' },
        include: {
          mainDimension: true,
          subDimension: true,
          aspect: true,
          subCategory: true,
        },
        orderBy: { calculationDate: 'desc' },
      });
    });

    it('should apply date range filter', async () => {
      const startDate = new Date('2024-01-01');
      const endDate = new Date('2024-01-31');

      (prisma.score.findMany as MockPrismaFunction).mockResolvedValue([]);

      await scoringService.getSymbolScores('sym-1', startDate, endDate);

      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          symbolId: 'sym-1',
          calculationDate: {
            gte: startDate,
            lte: endDate,
          },
        },
        include: {
          mainDimension: true,
          subDimension: true,
          aspect: true,
          subCategory: true,
        },
        orderBy: { calculationDate: 'desc' },
      });
    });
  });

  describe('getSymbolRankings', () => {
    it('should return symbol rankings', async () => {
      // Mock aggregate for rankings
      (prisma.score.aggregate as MockPrismaFunction).mockResolvedValue({
        _avg: {
          weightedValue: 85.5,
        },
      });

      // Mock findMany for scores
      (prisma.score.findMany as MockPrismaFunction).mockResolvedValue([
        {
          symbolId: 'sym-1',
          symbol: { symbol: 'فولاد', name: 'فولاد مبارکه اصفهان' },
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
        },
        {
          symbolId: 'sym-2',
          symbol: { symbol: 'خساپا', name: 'خودروسازی ایران خودرو' },
          weightedValue: 78.2,
          calculationDate: new Date('2024-01-01'),
        },
      ]);

      const result = await scoringService.getSymbolRankings();

      expect(result).toHaveLength(2);
      expect(result[0]).toHaveProperty('rank', 1);
      expect(result[1]).toHaveProperty('rank', 2);
    });

    it('should filter by dimension', async () => {
      (prisma.score.findMany as MockPrismaFunction).mockResolvedValue([]);

      await scoringService.getSymbolRankings({
        dimensionId: 'dim-1',
        limit: 10,
        offset: 0,
      });

      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          mainDimensionId: 'dim-1',
          calculationDate: expect.any(Object),
        },
        include: {
          symbol: true,
        },
        orderBy: { weightedValue: 'desc' },
        take: 10,
        skip: 0,
      });
    });

    it('should filter by score range', async () => {
      (prisma.score.findMany as MockPrismaFunction).mockResolvedValue([]);

      await scoringService.getSymbolRankings({
        minScore: 70,
        maxScore: 90,
      });

      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          weightedValue: {
            gte: 70,
            lte: 90,
          },
          calculationDate: expect.any(Object),
        },
        include: {
          symbol: true,
        },
        orderBy: { weightedValue: 'desc' },
      });
    });
  });

  describe('getLatestScores', () => {
    it('should return latest scores for all symbols', async () => {
      const mockScores = [
        {
          id: 'score-1',
          symbolId: 'sym-1',
          value: 85.5,
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
          mainDimension: {
            id: 'dim-1',
            code: 'TD-01',
            name: 'تحلیل تکنیکال',
          },
          symbol: {
            id: 'sym-1',
            symbol: 'فولاد',
            name: 'فولاد مبارکه اصفهان',
          },
        },
      ];

      (prisma.score.findMany as MockPrismaFunction).mockResolvedValue(mockScores);

      const result = await scoringService.getLatestScores();

      expect(result).toEqual(mockScores);
      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          calculationDate: expect.any(Object),
        },
        include: {
          mainDimension: true,
          symbol: true,
        },
        orderBy: { weightedValue: 'desc' },
      });
    });

    it('should filter by dimension', async () => {
      (prisma.score.findMany as MockPrismaFunction).mockResolvedValue([]);

      await scoringService.getLatestScores('dim-1');

      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          mainDimensionId: 'dim-1',
          calculationDate: expect.any(Object),
        },
        include: {
          mainDimension: true,
          symbol: true,
        },
        orderBy: { weightedValue: 'desc' },
      });
    });
  });

  describe('calculateScoreForElement', () => {
    it('should calculate score for main dimension', () => {
      const marketData = {
        rsi: 55.5,
        macd: 2.5,
        peg: 1.2,
        roe: 18.5,
      };

      const element = {
        code: 'TD-01',
        name: 'تحلیل تکنیکال',
      };

      const result = scoringService['calculateScoreForElement'](element, marketData);

      expect(result).toBeGreaterThanOrEqual(0);
      expect(result).toBeLessThanOrEqual(100);
    });

    it('should handle missing market data', () => {
      const marketData = {};
      const element = { code: 'TD-01' };

      const result = scoringService['calculateScoreForElement'](element, marketData);

      expect(result).toBe(0);
    });
  });
});