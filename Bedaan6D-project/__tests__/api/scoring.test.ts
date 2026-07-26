﻿import { describe, it, expect, beforeEach, vi, afterEach, Mock } from 'vitest';
import { createMocks } from 'node-mocks-http';
import { NextRequest } from 'next/server';
import { GET, POST } from '../../src/app/api/6d/scoring/route';
import { prisma } from '../../src/lib/prisma';

// Mock Prisma client
vi.mock('../../src/lib/prisma', () => ({
  prisma: {
    score: {
      findMany: vi.fn(),
      createMany: vi.fn(),
      aggregate: vi.fn(),
    },
    symbol: {
      findUnique: vi.fn(),
    },
    mainDimension: {
      findMany: vi.fn(),
    },
    $transaction: vi.fn((operations) => Promise.all(operations)),
  },
}));
// Type for mock functions
type MockPrismaFunction = Mock & {
  mockResolvedValue: (value: unknown) => void;
  mockRejectedValue: (error: Error) => void;
};

describe('API: /api/6d/scoring', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('POST /api/6d/scoring', () => {
    it('should calculate scores for a symbol', async () => {
      // Mock data
      const requestData = {
        symbolId: 'sym-1',
        date: '2024-01-01',
      };

      const mockSymbol = {
        id: 'sym-1',
        isin: 'IRO1FOLD0001',
        symbol: 'ÙÙˆÙ„Ø§Ø¯',
        name: 'ÙÙˆÙ„Ø§Ø¯ Ù…Ø¨Ø§Ø±Ú©Ù‡ Ø§ØµÙÙ‡Ø§Ù†',
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
          name: 'ØªØ­Ù„ÛŒÙ„ ØªÚ©Ù†ÛŒÚ©Ø§Ù„',
          weight: 1.0,
          order: 1,
          subDimensions: [
            {
              id: 'sub-1',
              code: 'TD-01-01',
              name: 'Ø´Ø§Ø®Øµâ€ŒÙ‡Ø§ÛŒ Ø±ÙˆÙ†Ø¯',
              weight: 1.0,
              order: 1,
              aspects: [
                {
                  id: 'asp-1',
                  code: 'TD-01-01-01',
                  name: 'Ù…ÛŒØ§Ù†Ú¯ÛŒÙ† Ù…ØªØ­Ø±Ú©',
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
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockSymbol);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockHierarchy);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue({ count: 5 });

      // Create mock request with JSON body
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/scoring',
        body: requestData,
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('success', true);
      expect(data).toHaveProperty('data');
      expect(data.data).toHaveProperty('symbolId', 'sym-1');
      expect(data.data).toHaveProperty('calculationDate');
      expect(data.data).toHaveProperty('dimensionScores');
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

    it('should validate required fields', async () => {
      // Invalid data - missing required fields
      const invalidData = {
        symbolId: '',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/scoring',
        body: invalidData,
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(400);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ø´Ù†Ø§Ø³Ù‡ Ù†Ù…Ø§Ø¯ Ø§Ù„Ø²Ø§Ù…ÛŒ Ø§Ø³Øª');
    });

    it('should validate date format', async () => {
      // Invalid date format
      const invalidData = {
        symbolId: 'sym-1',
        date: 'invalid-date',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/scoring',
        body: invalidData,
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(400);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('ÙØ±Ù…Øª ØªØ§Ø±ÛŒØ® Ù†Ø§Ù…Ø¹ØªØ¨Ø± Ø§Ø³Øª');
    });

    it('should handle non-existent symbol', async () => {
      // Mock non-existent symbol
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(null);

      const requestData = {
        symbolId: 'non-existent',
        date: '2024-01-01',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/scoring',
        body: requestData,
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(404);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ù†Ù…Ø§Ø¯ ÛŒØ§ÙØª Ù†Ø´Ø¯');
    });

    it('should handle missing market data', async () => {
      // Mock symbol without market data
      const mockSymbol = {
        id: 'sym-1',
        marketData: [],
      };

      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockSymbol);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue([]);

      const requestData = {
        symbolId: 'sym-1',
        date: '2024-01-01',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/scoring',
        body: requestData,
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(400);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ø¯Ø§Ø¯Ù‡â€ŒÙ‡Ø§ÛŒ Ø¨Ø§Ø²Ø§Ø± Ø¨Ø±Ø§ÛŒ Ù†Ù…Ø§Ø¯ ÛŒØ§ÙØª Ù†Ø´Ø¯');
    });

    it('should handle missing hierarchy', async () => {
      // Mock symbol with market data but no hierarchy
      const mockSymbol = {
        id: 'sym-1',
        marketData: [{ id: 'md-1', date: new Date('2024-01-01'), price: 15000 }],
      };

      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockSymbol);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue([]);

      const requestData = {
        symbolId: 'sym-1',
        date: '2024-01-01',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/scoring',
        body: requestData,
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(400);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ø³Ø§Ø®ØªØ§Ø± Ø³Ù„Ø³Ù„Ù‡â€ŒÙ…Ø±Ø§ØªØ¨ÛŒ ÛŒØ§ÙØª Ù†Ø´Ø¯');
    });

    it('should handle database errors', async () => {
      // Mock database error
      (prisma.$1 as MockPrismaFunction).mockRejectedValue(
        new Error('Database connection failed')
      );

      const requestData = {
        symbolId: 'sym-1',
        date: '2024-01-01',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/scoring',
        body: requestData,
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(500);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ø®Ø·Ø§ Ø¯Ø± Ù…Ø­Ø§Ø³Ø¨Ù‡ Ø§Ù…ØªÛŒØ§Ø²Ù‡Ø§');
    });

    it('should handle invalid JSON', async () => {
      // Create mock request with invalid JSON
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/scoring',
        body: 'invalid json',
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(400);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ø¯Ø§Ø¯Ù‡â€ŒÙ‡Ø§ÛŒ ÙˆØ±ÙˆØ¯ÛŒ Ù†Ø§Ù…Ø¹ØªØ¨Ø± Ø§Ø³Øª');
    });
  });

  describe('GET /api/6d/scoring', () => {
    it('should return scores for a symbol', async () => {
      // Mock data
      const mockScores = [
        {
          id: 'score-1',
          value: 85.5,
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
          mainDimension: {
            id: 'dim-1',
            code: 'TD-01',
            name: 'ØªØ­Ù„ÛŒÙ„ ØªÚ©Ù†ÛŒÚ©Ø§Ù„',
            weight: 1.0,
          },
          subDimension: null,
          aspect: null,
          subCategory: null,
        },
      ];

      // Mock Prisma call
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockScores);

      // Create mock request with query parameters
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring',
        query: {
          symbolId: 'sym-1',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('success', true);
      expect(data).toHaveProperty('data');
      expect(data.data).toHaveLength(1);
      expect(data.data[0].value).toBe(85.5);
      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          symbolId: 'sym-1',
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

    it('should apply date range filters', async () => {
      // Mock data
      const mockScores = [
        {
          id: 'score-1',
          value: 85.5,
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
          mainDimension: {
            id: 'dim-1',
            code: 'TD-01',
            name: 'ØªØ­Ù„ÛŒÙ„ ØªÚ©Ù†ÛŒÚ©Ø§Ù„',
          },
        },
      ];

      // Mock Prisma call
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockScores);

      // Create mock request with date range
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring',
        query: {
          symbolId: 'sym-1',
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
          symbolId: 'sym-1',
          calculationDate: {
            gte: expect.any(Date),
            lte: expect.any(Date),
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

    it('should filter by dimension', async () => {
      // Mock data
      const mockScores = [
        {
          id: 'score-1',
          value: 85.5,
          weightedValue: 85.5,
          calculationDate: new Date('2024-01-01'),
          mainDimension: {
            id: 'dim-1',
            code: 'TD-01',
            name: 'ØªØ­Ù„ÛŒÙ„ ØªÚ©Ù†ÛŒÚ©Ø§Ù„',
          },
        },
      ];

      // Mock Prisma call
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockScores);

      // Create mock request with dimension filter
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring',
        query: {
          symbolId: 'sym-1',
          dimensionId: 'dim-1',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);

      // Assert
      expect(response.status).toBe(200);
      expect(prisma.score.findMany).toHaveBeenCalledWith({
        where: {
          symbolId: 'sym-1',
          mainDimensionId: 'dim-1',
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

    it('should validate required symbolId for GET', async () => {
      // Create mock request without symbolId
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring',
        query: {},
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(400);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ø´Ù†Ø§Ø³Ù‡ Ù†Ù…Ø§Ø¯ Ø§Ù„Ø²Ø§Ù…ÛŒ Ø§Ø³Øª');
    });

    it('should handle empty scores', async () => {
      // Mock empty data
      (prisma.$1 as MockPrismaFunction).mockResolvedValue([]);

      // Create mock request
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring',
        query: {
          symbolId: 'sym-1',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('success', true);
      expect(data.data).toHaveLength(0);
    });

    it('should handle database errors in GET', async () => {
      // Mock database error
      (prisma.$1 as MockPrismaFunction).mockRejectedValue(
        new Error('Database connection failed')
      );

      // Create mock request
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/scoring',
        query: {
          symbolId: 'sym-1',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(500);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ø®Ø·Ø§ Ø¯Ø± Ø¯Ø±ÛŒØ§ÙØª Ø§Ù…ØªÛŒØ§Ø²Ù‡Ø§');
    });
  });
});

