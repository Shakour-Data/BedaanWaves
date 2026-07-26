import { describe, it, expect, beforeEach, vi, afterEach, Mock } from 'vitest';
import { createMocks } from 'node-mocks-http';
import { NextRequest } from 'next/server';
import { GET } from '../../src/app/api/6d/scoring/rankings/route';
import { prisma } from '../../src/lib/prisma';

// Mock Prisma client
vi.mock('../../src/lib/prisma', () => ({
  prisma: {
    score: {
      findMany: vi.fn(),
      aggregate: vi.fn(),
    },
    symbol: {
      findMany: vi.fn(),
    },
  },
}));

// Type for mock functions
type MockPrismaFunction = Mock & {
  mockResolvedValue: (value: unknown) => void;
  mockRejectedValue: (error: Error) => void;
};

describe('API: /api/6d/scoring/rankings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('GET /api/6d/scoring/rankings', () => {
    it('should return symbol rankings', async () => {
      // Mock data
      const mockRankings = [
        {
          symbolId: 'sym-1',
          symbol: {
            symbol: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯',
            name: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯ Ã™â€¦Ã˜Â¨Ã˜Â§Ã˜Â±ÃšÂ©Ã™â€¡ Ã˜Â§Ã˜ÂµÃ™ÂÃ™â€¡Ã˜Â§Ã™â€ ',
          },
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
        },
        {
          symbolId: 'sym-2',
          symbol: {
            symbol: 'Ã˜Â®Ã˜Â³Ã˜Â§Ã™Â¾Ã˜Â§',
            name: 'Ã˜Â®Ã™Ë†Ã˜Â¯Ã˜Â±Ã™Ë†Ã˜Â³Ã˜Â§Ã˜Â²Ã›Å’ Ã˜Â§Ã›Å’Ã˜Â±Ã˜Â§Ã™â€  Ã˜Â®Ã™Ë†Ã˜Â¯Ã˜Â±Ã™Ë†',
          },
          weightedValue: 78.2,
          calculationDate: new Date('2024-01-01'),
        },
      ];

      // Mock Prisma calls
      (prisma.score.findMany as MockPrismaFunction).mockResolvedValue(mockRankings);
      (prisma.score.aggregate as MockPrismaFunction).mockResolvedValue({
        _avg: {
          weightedValue: 81.85,
        },
      });

      // Create mock request
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring/rankings',
        query: {},
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);

      // Assert
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('success', true);
      expect(data).toHaveProperty('data');
      expect(data.data).toHaveProperty('rankings');
      expect(data.data.rankings).toHaveLength(2);
      expect(data.data.rankings[0]).toHaveProperty('rank', 1);
      expect(data.data.rankings[0]).toHaveProperty('score', 85.5);
      expect(data.data.rankings[0]).toHaveProperty('symbolCode', 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯');
      expect(data.data.rankings[1]).toHaveProperty('rank', 2);
      expect(data.data.rankings[1]).toHaveProperty('score', 78.2);
      expect(data.data).toHaveProperty('averageScore', 81.85);
      expect(data.data).toHaveProperty('pagination');
      expect(data.data.pagination).toHaveProperty('total', 2);
      expect(data.data.pagination).toHaveProperty('page', 1);
      expect(data.data.pagination).toHaveProperty('limit', 20);

      // Verify Prisma call
      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          calculationDate: expect.any(Object),
        },
        include: {
          symbol: true,
        },
        orderBy: { weightedValue: 'desc' },
        take: 20,
        skip: 0,
      });
    });

    it('should filter by dimension', async () => {
      // Mock data
      const mockRankings = [
        {
          symbolId: 'sym-1',
          symbol: {
            symbol: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯',
            name: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯ Ã™â€¦Ã˜Â¨Ã˜Â§Ã˜Â±ÃšÂ©Ã™â€¡ Ã˜Â§Ã˜ÂµÃ™ÂÃ™â€¡Ã˜Â§Ã™â€ ',
          },
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
        },
      ];

      // Mock Prisma calls
      (prisma.score.findMany as MockPrismaFunction).mockResolvedValue(mockRankings);
      (prisma.score.aggregate as MockPrismaFunction).mockResolvedValue({
        _avg: {
          weightedValue: 85.5,
        },
      });

      // Create mock request with dimension filter
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring/rankings',
        query: {
          dimensionId: 'dim-1',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);

      // Assert
      expect(response.status).toBe(200);
      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          mainDimensionId: 'dim-1',
          calculationDate: expect.any(Object),
        },
        include: {
          symbol: true,
        },
        orderBy: { weightedValue: 'desc' },
        take: 20,
        skip: 0,
      });
    });

    it('should apply pagination', async () => {
      // Mock data
      const mockRankings = Array(10).fill(null).map((_, i) => ({
        symbolId: `sym-${i + 1}`,
        symbol: {
          symbol: `نماد${i + 1}`,
          name: `شرکت ${i + 1}`,
        },
        weightedValue: 90 - i,
        calculationDate: new Date('2024-01-01'),
      }));

      // Mock Prisma calls
      (prisma.score.findMany as MockPrismaFunction).mockResolvedValue(mockRankings.slice(5, 10));
      (prisma.score.aggregate as MockPrismaFunction).mockResolvedValue({
        _avg: {
          weightedValue: 85,
        },
      });

      // Create mock request with pagination
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring/rankings',
        query: {
          page: '2',
          limit: '5',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(200);
      expect(data.data.rankings).toHaveLength(5);
      expect(data.data.pagination.page).toBe(2);
      expect(data.data.pagination.limit).toBe(5);
      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          calculationDate: expect.any(Object),
        },
        include: {
          symbol: true,
        },
        orderBy: { weightedValue: 'desc' },
        take: 5,
        skip: 5,
      });
    });

    it('should filter by score range', async () => {
      // Mock data
      const mockRankings = [
        {
          symbolId: 'sym-1',
          symbol: {
            symbol: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯',
            name: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯ Ã™â€¦Ã˜Â¨Ã˜Â§Ã˜Â±ÃšÂ©Ã™â€¡ Ã˜Â§Ã˜ÂµÃ™ÂÃ™â€¡Ã˜Â§Ã™â€ ',
          },
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
        },
      ];

      // Mock Prisma calls
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockRankings);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue({
        _avg: {
          weightedValue: 85.5,
        },
      });

      // Create mock request with score range
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring/rankings',
        query: {
          minScore: '70',
          maxScore: '90',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);

      // Assert
      expect(response.status).toBe(200);
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
        take: 20,
        skip: 0,
      });
    });

    it('should filter by market', async () => {
      // Mock data
      const mockSymbols = [
        {
          id: 'sym-1',
          symbol: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯',
          name: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯ Ã™â€¦Ã˜Â¨Ã˜Â§Ã˜Â±ÃšÂ©Ã™â€¡ Ã˜Â§Ã˜ÂµÃ™ÂÃ™â€¡Ã˜Â§Ã™â€ ',
          market: 'Ã˜Â¨Ã™Ë†Ã˜Â±Ã˜Â³',
        },
      ];

      const mockRankings = [
        {
          symbolId: 'sym-1',
          symbol: mockSymbols[0],
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
        },
      ];

      // Mock Prisma calls
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockSymbols);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockRankings);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue({
        _avg: {
          weightedValue: 85.5,
        },
      });

      // Create mock request with market filter
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring/rankings',
        query: {
          market: 'Ã˜Â¨Ã™Ë†Ã˜Â±Ã˜Â³',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);

      // Assert
      expect(response.status).toBe(200);
      expect(prisma.symbol.findMany).toHaveBeenCalledWith({
        where: {
          market: 'Ã˜Â¨Ã™Ë†Ã˜Â±Ã˜Â³',
        },
        select: {
          id: true,
        },
      });
      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          symbolId: {
            in: ['sym-1'],
          },
          calculationDate: expect.any(Object),
        },
        include: {
          symbol: true,
        },
        orderBy: { weightedValue: 'desc' },
        take: 20,
        skip: 0,
      });
    });

    it('should filter by sector', async () => {
      // Mock data
      const mockSymbols = [
        {
          id: 'sym-1',
          symbol: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯',
          name: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯ Ã™â€¦Ã˜Â¨Ã˜Â§Ã˜Â±ÃšÂ©Ã™â€¡ Ã˜Â§Ã˜ÂµÃ™ÂÃ™â€¡Ã˜Â§Ã™â€ ',
          sector: 'Ã™ÂÃ™â€žÃ˜Â²Ã˜Â§Ã˜Âª Ã˜Â§Ã˜Â³Ã˜Â§Ã˜Â³Ã›Å’',
        },
      ];

      const mockRankings = [
        {
          symbolId: 'sym-1',
          symbol: mockSymbols[0],
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
        },
      ];

      // Mock Prisma calls
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockSymbols);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockRankings);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue({
        _avg: {
          weightedValue: 85.5,
        },
      });

      // Create mock request with sector filter
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring/rankings',
        query: {
          sector: 'Ã™ÂÃ™â€žÃ˜Â²Ã˜Â§Ã˜Âª Ã˜Â§Ã˜Â³Ã˜Â§Ã˜Â³Ã›Å’',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);

      // Assert
      expect(response.status).toBe(200);
      expect(prisma.symbol.findMany).toHaveBeenCalledWith({
        where: {
          sector: 'Ã™ÂÃ™â€žÃ˜Â²Ã˜Â§Ã˜Âª Ã˜Â§Ã˜Â³Ã˜Â§Ã˜Â³Ã›Å’',
        },
        select: {
          id: true,
        },
      });
    });

    it('should handle empty rankings', async () => {
      // Mock empty data
      (prisma.$1 as MockPrismaFunction).mockResolvedValue([]);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue({
        _avg: {
          weightedValue: null,
        },
      });

      // Create mock request
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring/rankings',
        query: {},
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(200);
      expect(data.data.rankings).toHaveLength(0);
      expect(data.data.averageScore).toBeNull();
      expect(data.data.pagination.total).toBe(0);
    });

    it('should handle invalid query parameters', async () => {
      // Mock data
      const mockRankings = [
        {
          symbolId: 'sym-1',
          symbol: {
            symbol: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯',
            name: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯ Ã™â€¦Ã˜Â¨Ã˜Â§Ã˜Â±ÃšÂ©Ã™â€¡ Ã˜Â§Ã˜ÂµÃ™ÂÃ™â€¡Ã˜Â§Ã™â€ ',
          },
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
        },
      ];

      // Mock Prisma calls
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockRankings);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue({
        _avg: {
          weightedValue: 85.5,
        },
      });

      // Create mock request with invalid parameters
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring/rankings',
        query: {
          page: 'invalid',
          limit: 'invalid',
          minScore: 'invalid',
          maxScore: 'invalid',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(200); // Should still return 200 with defaults
      expect(data.data.pagination.page).toBe(1);
      expect(data.data.pagination.limit).toBe(20);
    });

    it('should handle database errors', async () => {
      // Mock database error
      (prisma.$1 as MockPrismaFunction).mockRejectedValue(
        new Error('Database connection failed')
      );

      // Create mock request
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring/rankings',
        query: {},
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(500);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ã˜Â®Ã˜Â·Ã˜Â§ Ã˜Â¯Ã˜Â± Ã˜Â¯Ã˜Â±Ã›Å’Ã˜Â§Ã™ÂÃ˜Âª Ã˜Â±Ã˜ÂªÃ˜Â¨Ã™â€¡Ã¢â‚¬Å’Ã˜Â¨Ã™â€ Ã˜Â¯Ã›Å’');
    });

    it('should handle date range filters', async () => {
      // Mock data
      const mockRankings = [
        {
          symbolId: 'sym-1',
          symbol: {
            symbol: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯',
            name: 'Ã™ÂÃ™Ë†Ã™â€žÃ˜Â§Ã˜Â¯ Ã™â€¦Ã˜Â¨Ã˜Â§Ã˜Â±ÃšÂ©Ã™â€¡ Ã˜Â§Ã˜ÂµÃ™ÂÃ™â€¡Ã˜Â§Ã™â€ ',
          },
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-15'),
        },
      ];

      // Mock Prisma calls
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockRankings);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue({
        _avg: {
          weightedValue: 85.5,
        },
      });

      // Create mock request with date range
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring/rankings',
        query: {
          startDate: '2024-01-01',
          endDate: '2024-01-31',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);

      // Assert
      expect(response.status).toBe(200);
      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          calculationDate: {
            gte: expect.any(Date),
            lte: expect.any(Date),
          },
        },
        include: {
          symbol: true,
        },
        orderBy: { weightedValue: 'desc' },
        take: 20,
        skip: 0,
      });
    });
  });
});

