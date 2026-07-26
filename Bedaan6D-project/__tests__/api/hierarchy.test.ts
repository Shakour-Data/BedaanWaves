﻿import { describe, it, expect, beforeEach, vi, afterEach, Mock } from 'vitest';
import { createMocks } from 'node-mocks-http';
import { NextRequest } from 'next/server';
import { GET, POST } from '../../src/app/api/6d/hierarchy/route';
import { prisma } from '../../src/lib/prisma';

// Mock Prisma client
vi.mock('../../src/lib/prisma', () => ({
  prisma: {
    mainDimension: {
      findMany: vi.fn(),
      create: vi.fn(),
    },
  },
}));

// Type for mock functions
type MockPrismaFunction = Mock & {
  mockResolvedValue: (value: unknown) => void;
  mockRejectedValue: (error: Error) => void;
};



describe('API: /api/6d/hierarchy', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('GET /api/6d/hierarchy', () => {
    it('should return full hierarchy structure', async () => {
      // Mock data
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

      // Mock Prisma call
      (prisma.mainDimension.findMany as MockPrismaFunction).mockResolvedValue(mockHierarchy);

      // Create mock request
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/hierarchy',
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('success', true);
      expect(data).toHaveProperty('data');
      expect(data.data).toHaveProperty('mainDimensions');
      expect(data.data.mainDimensions).toHaveLength(1);
      expect(data.data.mainDimensions[0].code).toBe('TD-01');
    });

    it('should handle empty hierarchy', async () => {
      // Mock empty data
      (prisma.mainDimension.findMany as MockPrismaFunction).mockResolvedValue([]);

      // Create mock request
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/hierarchy',
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(200);
      expect(data).toHaveProperty('success', true);
      expect(data.data.mainDimensions).toHaveLength(0);
    });

    it('should handle database errors', async () => {
      // Mock database error
      (prisma.mainDimension.findMany as MockPrismaFunction).mockRejectedValue(
        new Error('Database connection failed')
      );

      // Create mock request
      const { req } = createMocks({
        method: 'GET',
        url: '/api/6d/hierarchy',
      });

      // Execute
      const response = await GET(req as unknown as NextRequest);
      const data = await response.json();

      // Assert
      expect(response.status).toBe(500);
      expect(data).toHaveProperty('success', false);
      expect(data).toHaveProperty('error');
      expect(data.error).toContain('Ø®Ø·Ø§ Ø¯Ø± Ø¯Ø±ÛŒØ§ÙØª Ø³Ø§Ø®ØªØ§Ø± Ø³Ù„Ø³Ù„Ù‡â€ŒÙ…Ø±Ø§ØªØ¨ÛŒ');
    });
  });

  describe('POST /api/6d/hierarchy', () => {
    it('should create a new main dimension', async () => {
      // Mock data
      const requestData = {
        code: 'TD-02',
        name: 'ØªØ­Ù„ÛŒÙ„ Ø¨Ù†ÛŒØ§Ø¯ÛŒ',
        description: 'ØªØ­Ù„ÛŒÙ„ Ø¨Ù†ÛŒØ§Ø¯ÛŒ Ø´Ø±Ú©Øªâ€ŒÙ‡Ø§',
        weight: 1.0,
        order: 2,
      };

      const mockCreated = {
        id: 'dim-2',
        ...requestData,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      // Mock Prisma call
      (prisma.mainDimension.create as MockPrismaFunction).mockResolvedValue(mockCreated);

      // Create mock request with JSON body
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/hierarchy',
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
      expect(data).toHaveProperty('data');
      expect(data.data).toHaveProperty('id', 'dim-2');
      expect(data.data.code).toBe('TD-02');
      expect(prisma.mainDimension.create).toHaveBeenCalledWith({
        data: requestData,
      });
    });

    it('should validate required fields', async () => {
      // Invalid data - missing required fields
      const invalidData = {
        code: '',
        name: '',
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/hierarchy',
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
      expect(data).toHaveProperty('error');
      expect(data.error).toContain('Ú©Ø¯ Ø¨Ø¹Ø¯ Ø§ØµÙ„ÛŒ Ø§Ù„Ø²Ø§Ù…ÛŒ Ø§Ø³Øª');
    });

    it('should handle duplicate code error', async () => {
      // Mock duplicate error
      (prisma.mainDimension.create as MockPrismaFunction).mockRejectedValue({
        code: 'P2002',
        meta: { target: ['code'] },
      });

      const requestData = {
        code: 'TD-01',
        name: 'ØªØ­Ù„ÛŒÙ„ ØªÚ©Ù†ÛŒÚ©Ø§Ù„',
        order: 1,
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/hierarchy',
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
      expect(data.error).toContain('Ú©Ø¯ Ø¨Ø¹Ø¯ Ø§ØµÙ„ÛŒ ØªÚ©Ø±Ø§Ø±ÛŒ Ø§Ø³Øª');
    });

    it('should handle invalid JSON', async () => {
      // Create mock request with invalid JSON
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/hierarchy',
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

    it('should validate weight range', async () => {
      // Invalid weight
      const invalidData = {
        code: 'TD-03',
        name: 'ØªØ­Ù„ÛŒÙ„ Ø±ÙˆØ§Ù†Ø´Ù†Ø§Ø³ÛŒ',
        weight: -1.0,
        order: 3,
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/hierarchy',
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
      expect(data.error).toContain('ÙˆØ²Ù† Ø¨Ø§ÛŒØ¯ Ø¨ÛŒÙ† 0 Ùˆ 10 Ø¨Ø§Ø´Ø¯');
    });

    it('should validate order uniqueness', async () => {
      // Mock duplicate order error
      (prisma.mainDimension.create as MockPrismaFunction).mockRejectedValue({
        code: 'P2002',
        meta: { target: ['order'] },
      });

      const requestData = {
        code: 'TD-04',
        name: 'ØªØ­Ù„ÛŒÙ„ Ú©Ù…ÛŒ',
        order: 1, // Duplicate order
      };

      // Create mock request
      const { req } = createMocks({
        method: 'POST',
        url: '/api/6d/hierarchy',
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
      expect(data.error).toContain('ØªØ±ØªÛŒØ¨ Ø¨Ø¹Ø¯ Ø§ØµÙ„ÛŒ ØªÚ©Ø±Ø§Ø±ÛŒ Ø§Ø³Øª');
    });
  });
});
