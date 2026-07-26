import { describe, it, expect, beforeEach, vi, Mock } from 'vitest';
import { HierarchyService } from '../../src/services/hierarchy-service';
import { prisma } from '../../src/lib/prisma';

// Type for mock functions
type MockPrismaFunction = Mock & {
  mockResolvedValue: (value: unknown) => void;
  mockRejectedValue: (error: Error) => void;
};

// Mock Prisma client
vi.mock('../../src/lib/prisma', () => ({
  prisma: {
    mainDimension: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    subDimension: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    aspect: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
    subCategory: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
  },
}));

describe('HierarchyService', () => {
  let hierarchyService: HierarchyService;

  beforeEach(() => {
    hierarchyService = new HierarchyService();
    vi.clearAllMocks();
  });

  describe('getFullHierarchy', () => {
    it('should return full hierarchy structure', async () => {
      // Mock data
      const mockMainDimensions = [
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
      (prisma.mainDimension.findMany as MockPrismaFunction).mockResolvedValue(mockMainDimensions);

      // Execute
      const result = await hierarchyService.getFullHierarchy();

      // Assert
      expect(result).toHaveProperty('mainDimensions');
      expect(result.mainDimensions).toHaveLength(1);
      expect(result.mainDimensions[0].code).toBe('TD-01');
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

    it('should handle empty hierarchy', async () => {
      // Mock empty data
      (prisma.mainDimension.findMany as MockPrismaFunction).mockResolvedValue([]);

      // Execute
      const result = await hierarchyService.getFullHierarchy();

      // Assert
      expect(result).toHaveProperty('mainDimensions');
      expect(result.mainDimensions).toHaveLength(0);
    });
  });

  describe('createMainDimension', () => {
    it('should create a new main dimension', async () => {
      const mockData = {
        code: 'TD-02',
        name: 'تحلیل بنیادی',
        description: 'تحلیل بنیادی شرکت‌ها',
        weight: 1.0,
        order: 2,
      };

      const mockCreated = {
        id: 'dim-2',
        ...mockData,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      (prisma.mainDimension.create as MockPrismaFunction).mockResolvedValue(mockCreated);

      const result = await hierarchyService.createMainDimension(mockData);

      expect(result).toEqual(mockCreated);
      expect(prisma.mainDimension.create).toHaveBeenCalledWith({
        data: mockData,
      });
    });

    it('should validate required fields', async () => {
      const invalidData = {
        code: '',
        name: '',
        order: 0,
      };

      await expect(hierarchyService.createMainDimension(invalidData))
        .rejects
        .toThrow();
    });
  });

  describe('getMainDimension', () => {
    it('should return main dimension by id', async () => {
      const mockDimension = {
        id: 'dim-1',
        code: 'TD-01',
        name: 'تحلیل تکنیکال',
        weight: 1.0,
        order: 1,
        subDimensions: [],
      };

      (prisma.mainDimension.findUnique as MockPrismaFunction).mockResolvedValue(mockDimension);

      const result = await hierarchyService.getMainDimension('dim-1');

      expect(result).toEqual(mockDimension);
      expect(prisma.mainDimension.findUnique).toHaveBeenCalledWith({
        where: { id: 'dim-1' },
        include: { subDimensions: true },
      });
    });

    it('should return null for non-existent dimension', async () => {
      (prisma.mainDimension.findUnique as MockPrismaFunction).mockResolvedValue(null);

      const result = await hierarchyService.getMainDimension('non-existent');

      expect(result).toBeNull();
    });
  });

  describe('updateMainDimension', () => {
    it('should update main dimension', async () => {
      const updateData = {
        name: 'تحلیل تکنیکال پیشرفته',
        weight: 1.2,
      };

      const mockUpdated = {
        id: 'dim-1',
        code: 'TD-01',
        name: 'تحلیل تکنیکال پیشرفته',
        weight: 1.2,
        order: 1,
      };

      (prisma.mainDimension.update as MockPrismaFunction).mockResolvedValue(mockUpdated);

      const result = await hierarchyService.updateMainDimension('dim-1', updateData);

      expect(result).toEqual(mockUpdated);
      expect(prisma.mainDimension.update).toHaveBeenCalledWith({
        where: { id: 'dim-1' },
        data: updateData,
      });
    });
  });

  describe('deleteMainDimension', () => {
    it('should delete main dimension', async () => {
      const mockDeleted = {
        id: 'dim-1',
        code: 'TD-01',
        name: 'تحلیل تکنیکال',
        weight: 1.0,
        order: 1,
      };

      (prisma.mainDimension.delete as MockPrismaFunction).mockResolvedValue(mockDeleted);

      const result = await hierarchyService.deleteMainDimension('dim-1');

      expect(result).toEqual(mockDeleted);
      expect(prisma.mainDimension.delete).toHaveBeenCalledWith({
        where: { id: 'dim-1' },
      });
    });
  });
});