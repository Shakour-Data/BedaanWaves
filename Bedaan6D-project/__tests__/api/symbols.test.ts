﻿import { describe, it, expect, beforeEach, vi, afterEach, Mock } from 'vitest';
import { createMocks } from 'node-mocks-http';
import { NextRequest } from 'next/server';
import { GET, POST } from '../../src/app/api/6d/symbols/route';
import { prisma } from '../../src/lib/prisma';

// Mock Prisma client
vi.mock('../../src/lib/prisma', () => ({
  prisma: {
    symbol: {
      findMany: vi.fn(),
      create: vi.fn(),
      count: vi.fn(),
    },
    marketData: {
      findMany: vi.fn(),
    },
  },
}));
// Type for mock functions
type MockPrismaFunction = Mock & {
  mockResolvedValue: (value: unknown) => void;
  mockRejectedValue: (error: Error) => void;
};

describe('API: /api/6d/symbols', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('GET /api/6d/symbols', () => {
    it('should return symbols with market data', async () => {
      // Mock data
      const mockSymbols = [
        {
          id: 'sym-1',
          isin: 'IRO1FOLD0001',
          symbol: 'ÙÙˆÙ„Ø§Ø¯',
          name: 'ÙÙˆÙ„Ø§Ø¯ Ù…Ø¨Ø§Ø±Ú©Ù‡ Ø§ØµÙÙ‡Ø§Ù†',
          market: 'Ø¨ÙˆØ±Ø³',
          sector: 'ÙÙ„Ø²Ø§Øª Ø§Ø³Ø§Ø³ÛŒ',
          subSector: 'ÙÙˆÙ„Ø§Ø¯',
          marketData: [
            {
              id: 'md-1',
              date: new Date('2024-01-01'),
              price: 15000,
              rsi: 55.5,
              macd: 2.5,
            },
          ],
        },
      ];

      // Mock Prisma calls
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockSymbols);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(1);

      // Create mock request
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/symbols',
        query: {},
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('success', true);
      expect(data).toHaveProperty('data');
      expect(data.data).toHaveProperty('symbols');
      expect(data.data.symbols).toHaveLength(1);
      expect(data.data.symbols[0].symbol).toBe('ÙÙˆÙ„Ø§Ø¯');
      expect(data.data).toHaveProperty('pagination');
      expect(data.data.pagination).toHaveProperty('total', 1);
      expect(data.data.pagination).toHaveProperty('page', 1);
      expect(data.data.pagination).toHaveProperty('limit', 20);
    });

    it('should apply query filters correctly', async () => {
      // Mock data
      const mockSymbols = [
        {
          id: 'sym-1',
          symbol: 'ÙÙˆÙ„Ø§Ø¯',
          name: 'ÙÙˆÙ„Ø§Ø¯ Ù…Ø¨Ø§Ø±Ú©Ù‡ Ø§ØµÙÙ‡Ø§Ù†',
          market: 'Ø¨ÙˆØ±Ø³',
          sector: 'ÙÙ„Ø²Ø§Øª Ø§Ø³Ø§Ø³ÛŒ',
          marketData: [],
        },
      ];

      // Mock Prisma calls
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockSymbols);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(1);

      // Create mock request with query parameters
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/symbols',
        query: {
          market: 'Ø¨ÙˆØ±Ø³',
          sector: 'ÙÙ„Ø²Ø§Øª Ø§Ø³Ø§Ø³ÛŒ',
          search: 'ÙÙˆÙ„Ø§Ø¯',
          page: '2',
          limit: '10',
        },
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);

      // Assert
      expect(response.status).toBe(200);
      expect(prisma.symbol.findMany).toHaveBeenCalledWith({
        where: {
          market: 'Ø¨ÙˆØ±Ø³',
          sector: 'ÙÙ„Ø²Ø§Øª Ø§Ø³Ø§Ø³ÛŒ',
          OR: [
            { symbol: { contains: 'ÙÙˆÙ„Ø§Ø¯', mode: 'insensitive' } },
            { name: { contains: 'ÙÙˆÙ„Ø§Ø¯', mode: 'insensitive' } },
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
        skip: 10,
      });
    });

    it('should handle empty result set', async () => {
      // Mock empty data
      (prisma.$1 as MockPrismaFunction).mockResolvedValue([]);
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(0);

      // Create mock request
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/symbols',
        query: {},
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(200);
      expect(data.data.symbols).toHaveLength(0);
      expect(data.data.pagination.total).toBe(0);
    });

    it('should handle invalid query parameters', async () => {
      // Create mock request with invalid parameters
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/symbols',
        query: {
          page: 'invalid',
          limit: 'invalid',
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
        url: '/api/6d/symbols',
        query: {},
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(500);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ø®Ø·Ø§ Ø¯Ø± Ø¯Ø±ÛŒØ§ÙØª Ù†Ù…Ø§Ø¯Ù‡Ø§');
    });
  });

  describe('POST /api/6d/symbols', () => {
    it('should create a new symbol', async () => {
      // Mock data
      const requestData = {
        isin: 'IRO1FOLD0001',
        symbol: 'ÙÙˆÙ„Ø§Ø¯',
        name: 'ÙÙˆÙ„Ø§Ø¯ Ù…Ø¨Ø§Ø±Ú©Ù‡ Ø§ØµÙÙ‡Ø§Ù†',
        market: 'Ø¨ÙˆØ±Ø³',
        sector: 'ÙÙ„Ø²Ø§Øª Ø§Ø³Ø§Ø³ÛŒ',
        subSector: 'ÙÙˆÙ„Ø§Ø¯',
      };

      const mockCreated = {
        id: 'sym-1',
        ...requestData,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      // Mock Prisma call
      (prisma.$1 as MockPrismaFunction).mockResolvedValue(mockCreated);

      // Create mock request with JSON body
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/symbols',
        body: requestData,
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(201);
      expect(data).toHaveProperty('success', true);
      expect(data.data).toHaveProperty('id', 'sym-1');
      expect(data.data.symbol).toBe('ÙÙˆÙ„Ø§Ø¯');
      expect(prisma.symbol.create).toHaveBeenCalledWith({
        data: requestData,
      });
    });

    it('should validate required fields', async () => {
      // Invalid data - missing required fields
      const invalidData = {
        isin: '',
        symbol: '',
        name: '',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/symbols',
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
      expect(data.error).toContain('Ú©Ø¯ ISIN Ø§Ù„Ø²Ø§Ù…ÛŒ Ø§Ø³Øª');
    });

    it('should validate ISIN format', async () => {
      // Invalid ISIN format
      const invalidData = {
        isin: 'invalid-isin',
        symbol: 'ÙÙˆÙ„Ø§Ø¯',
        name: 'ÙÙˆÙ„Ø§Ø¯ Ù…Ø¨Ø§Ø±Ú©Ù‡ Ø§ØµÙÙ‡Ø§Ù†',
        market: 'Ø¨ÙˆØ±Ø³',
        sector: 'ÙÙ„Ø²Ø§Øª Ø§Ø³Ø§Ø³ÛŒ',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/symbols',
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
      expect(data.error).toContain('ÙØ±Ù…Øª Ú©Ø¯ ISIN Ù†Ø§Ù…Ø¹ØªØ¨Ø± Ø§Ø³Øª');
    });

    it('should handle duplicate ISIN error', async () => {
      // Mock duplicate error
      (prisma.$1 as MockPrismaFunction).mockRejectedValue({
        code: 'P2002',
        meta: { target: ['isin'] },
      });

      const requestData = {
        isin: 'IRO1FOLD0001',
        symbol: 'ÙÙˆÙ„Ø§Ø¯',
        name: 'ÙÙˆÙ„Ø§Ø¯ Ù…Ø¨Ø§Ø±Ú©Ù‡ Ø§ØµÙÙ‡Ø§Ù†',
        market: 'Ø¨ÙˆØ±Ø³',
        sector: 'ÙÙ„Ø²Ø§Øª Ø§Ø³Ø§Ø³ÛŒ',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/symbols',
        body: requestData,
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(409);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ú©Ø¯ ISIN ØªÚ©Ø±Ø§Ø±ÛŒ Ø§Ø³Øª');
    });

    it('should handle duplicate symbol error', async () => {
      // Mock duplicate error
      (prisma.$1 as MockPrismaFunction).mockRejectedValue({
        code: 'P2002',
        meta: { target: ['symbol'] },
      });

      const requestData = {
        isin: 'IRO1FOLD0002',
        symbol: 'ÙÙˆÙ„Ø§Ø¯',
        name: 'ÙÙˆÙ„Ø§Ø¯ Ù…Ø¨Ø§Ø±Ú©Ù‡ Ø§ØµÙÙ‡Ø§Ù†',
        market: 'Ø¨ÙˆØ±Ø³',
        sector: 'ÙÙ„Ø²Ø§Øª Ø§Ø³Ø§Ø³ÛŒ',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/symbols',
        body: requestData,
        headers: {
          'content-type': 'application/json',
        },
      });

      // Execute
      const response = await POST(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(409);
      expect(data).toHaveProperty('success', false);
      expect(data.error).toContain('Ù†Ù…Ø§Ø¯ ØªÚ©Ø±Ø§Ø±ÛŒ Ø§Ø³Øª');
    });

    it('should validate market values', async () => {
      // Invalid market value
      const invalidData = {
        isin: 'IRO1FOLD0001',
        symbol: 'ÙÙˆÙ„Ø§Ø¯',
        name: 'ÙÙˆÙ„Ø§Ø¯ Ù…Ø¨Ø§Ø±Ú©Ù‡ Ø§ØµÙÙ‡Ø§Ù†',
        market: 'invalid-market',
        sector: 'ÙÙ„Ø²Ø§Øª Ø§Ø³Ø§Ø³ÛŒ',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/symbols',
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
      expect(data.error).toContain('Ø¨Ø§Ø²Ø§Ø± Ù†Ø§Ù…Ø¹ØªØ¨Ø± Ø§Ø³Øª');
    });

    it('should handle invalid JSON', async () => {
      // Create mock request with invalid JSON
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/symbols',
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
});

