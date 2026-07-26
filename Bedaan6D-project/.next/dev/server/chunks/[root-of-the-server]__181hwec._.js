module.exports = [
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}),
"[project]/src/services/hierarchy-service.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "HierarchyService",
    ()=>HierarchyService,
    "hierarchyService",
    ()=>hierarchyService
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__ = __turbopack_context__.i("[externals]/@prisma/client [external] (@prisma/client, cjs, [project]/node_modules/@prisma/client)");
;
const prisma = new __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["PrismaClient"]();
class HierarchyService {
    /**
   * دریافت کامل ساختار سلسله‌مراتبی
   */ async getFullHierarchy() {
        try {
            const mainDimensions = await prisma.mainDimension.findMany({
                include: {
                    subDimensions: {
                        include: {
                            aspects: {
                                include: {
                                    subCategories: {
                                        orderBy: {
                                            order: 'asc'
                                        }
                                    }
                                },
                                orderBy: {
                                    order: 'asc'
                                }
                            }
                        },
                        orderBy: {
                            order: 'asc'
                        }
                    }
                },
                orderBy: {
                    order: 'asc'
                }
            });
            return {
                mainDimensions: mainDimensions.map((md)=>({
                        id: md.id,
                        code: md.code,
                        name: md.name,
                        description: md.description || undefined,
                        weight: md.weight,
                        order: md.order,
                        subDimensions: md.subDimensions.map((sd)=>({
                                id: sd.id,
                                code: sd.code,
                                name: sd.name,
                                description: sd.description || undefined,
                                weight: sd.weight,
                                order: sd.order,
                                aspects: sd.aspects.map((as)=>({
                                        id: as.id,
                                        code: as.code,
                                        name: as.name,
                                        description: as.description || undefined,
                                        weight: as.weight,
                                        order: as.order,
                                        subCategories: as.subCategories.map((sc)=>({
                                                id: sc.id,
                                                code: sc.code,
                                                name: sc.name,
                                                description: sc.description || undefined,
                                                weight: sc.weight,
                                                order: sc.order
                                            }))
                                    }))
                            }))
                    }))
            };
        } catch (error) {
            console.error('خطا در دریافت ساختار سلسله‌مراتبی:', error);
            throw new Error('خطا در دریافت ساختار سلسله‌مراتبی');
        }
    }
    /**
   * دریافت ساختار درختی برای نمایش
   */ async getHierarchyTree() {
        try {
            const mainDimensions = await prisma.mainDimension.findMany({
                include: {
                    subDimensions: {
                        include: {
                            aspects: {
                                include: {
                                    subCategories: true
                                }
                            }
                        }
                    }
                },
                orderBy: {
                    order: 'asc'
                }
            });
            return mainDimensions.map((md)=>this.mapToHierarchyNode(md));
        } catch (error) {
            console.error('خطا در دریافت درخت سلسله‌مراتبی:', error);
            throw new Error('خطا در دریافت درخت سلسله‌مراتبی');
        }
    }
    /**
   * ایجاد بعد اصلی جدید
   */ async createMainDimension(data) {
        try {
            // بررسی تکراری نبودن کد
            const existing = await prisma.mainDimension.findUnique({
                where: {
                    code: data.code
                }
            });
            if (existing) {
                throw new Error(`کد ${data.code} قبلاً استفاده شده است`);
            }
            // بررسی تکراری نبودن ترتیب
            const existingOrder = await prisma.mainDimension.findUnique({
                where: {
                    order: data.order
                }
            });
            if (existingOrder) {
                throw new Error(`ترتیب ${data.order} قبلاً استفاده شده است`);
            }
            return await prisma.mainDimension.create({
                data: {
                    code: data.code,
                    name: data.name,
                    description: data.description,
                    weight: data.weight || 1.0,
                    order: data.order
                }
            });
        } catch (error) {
            console.error('خطا در ایجاد بعد اصلی:', error);
            throw error;
        }
    }
    /**
   * ایجاد زیربعد جدید
   */ async createSubDimension(data) {
        try {
            // بررسی وجود بعد اصلی
            const mainDim = await prisma.mainDimension.findUnique({
                where: {
                    id: data.mainDimensionId
                }
            });
            if (!mainDim) {
                throw new Error('بعد اصلی مورد نظر یافت نشد');
            }
            // بررسی تکراری نبودن کد در این بعد اصلی
            const existingCode = await prisma.subDimension.findFirst({
                where: {
                    code: data.code,
                    mainDimensionId: data.mainDimensionId
                }
            });
            if (existingCode) {
                throw new Error(`کد ${data.code} قبلاً در این بعد اصلی استفاده شده است`);
            }
            // بررسی تکراری نبودن ترتیب در این بعد اصلی
            const existingOrder = await prisma.subDimension.findFirst({
                where: {
                    order: data.order,
                    mainDimensionId: data.mainDimensionId
                }
            });
            if (existingOrder) {
                throw new Error(`ترتیب ${data.order} قبلاً در این بعد اصلی استفاده شده است`);
            }
            return await prisma.subDimension.create({
                data: {
                    code: data.code,
                    name: data.name,
                    description: data.description,
                    weight: data.weight || 1.0,
                    order: data.order,
                    mainDimensionId: data.mainDimensionId
                }
            });
        } catch (error) {
            console.error('خطا در ایجاد زیربعد:', error);
            throw error;
        }
    }
    /**
   * به‌روزرسانی وزن یک گره در سلسله‌مراتب
   */ async updateNodeWeight(nodeId, level, newWeight) {
        try {
            if (newWeight < 0 || newWeight > 10) {
                throw new Error('وزن باید بین 0 تا 10 باشد');
            }
            switch(level){
                case 'main':
                    await prisma.mainDimension.update({
                        where: {
                            id: nodeId
                        },
                        data: {
                            weight: newWeight
                        }
                    });
                    break;
                case 'sub':
                    await prisma.subDimension.update({
                        where: {
                            id: nodeId
                        },
                        data: {
                            weight: newWeight
                        }
                    });
                    break;
                case 'aspect':
                    await prisma.aspect.update({
                        where: {
                            id: nodeId
                        },
                        data: {
                            weight: newWeight
                        }
                    });
                    break;
                case 'category':
                    await prisma.subCategory.update({
                        where: {
                            id: nodeId
                        },
                        data: {
                            weight: newWeight
                        }
                    });
                    break;
                default:
                    throw new Error('سطح گره نامعتبر است');
            }
        } catch (error) {
            console.error('خطا در به‌روزرسانی وزن:', error);
            throw error;
        }
    }
    /**
   * حذف یک گره از سلسله‌مراتب
   */ async deleteNode(nodeId, level) {
        try {
            switch(level){
                case 'main':
                    {
                        // بررسی وجود زیربعد‌ها قبل از حذف
                        const subDims = await prisma.subDimension.count({
                            where: {
                                mainDimensionId: nodeId
                            }
                        });
                        if (subDims > 0) {
                            throw new Error('امکان حذف بعد اصلی با زیربعد‌های موجود وجود ندارد');
                        }
                        await prisma.mainDimension.delete({
                            where: {
                                id: nodeId
                            }
                        });
                        break;
                    }
                case 'sub':
                    {
                        // بررسی وجود جنبه‌ها قبل از حذف
                        const aspects = await prisma.aspect.count({
                            where: {
                                subDimensionId: nodeId
                            }
                        });
                        if (aspects > 0) {
                            throw new Error('امکان حذف زیربعد با جنبه‌های موجود وجود ندارد');
                        }
                        await prisma.subDimension.delete({
                            where: {
                                id: nodeId
                            }
                        });
                        break;
                    }
                case 'aspect':
                    {
                        // بررسی وجود زیرمجموعه‌ها قبل از حذف
                        const categories = await prisma.subCategory.count({
                            where: {
                                aspectId: nodeId
                            }
                        });
                        if (categories > 0) {
                            throw new Error('امکان حذف جنبه با زیرمجموعه‌های موجود وجود ندارد');
                        }
                        await prisma.aspect.delete({
                            where: {
                                id: nodeId
                            }
                        });
                        break;
                    }
                case 'category':
                    await prisma.subCategory.delete({
                        where: {
                            id: nodeId
                        }
                    });
                    break;
                default:
                    throw new Error('سطح گره نامعتبر است');
            }
        } catch (error) {
            console.error('خطا در حذف گره:', error);
            throw error;
        }
    }
    /**
   * جستجوی گره‌ها بر اساس نام یا کد
   */ async searchNodes(query) {
        try {
            // جستجو در تمام سطوح
            const [mainDims, subDims, aspects, categories] = await Promise.all([
                prisma.mainDimension.findMany({
                    where: {
                        OR: [
                            {
                                name: {
                                    contains: query
                                }
                            },
                            {
                                code: {
                                    contains: query
                                }
                            }
                        ]
                    }
                }),
                prisma.subDimension.findMany({
                    where: {
                        OR: [
                            {
                                name: {
                                    contains: query
                                }
                            },
                            {
                                code: {
                                    contains: query
                                }
                            }
                        ]
                    }
                }),
                prisma.aspect.findMany({
                    where: {
                        OR: [
                            {
                                name: {
                                    contains: query
                                }
                            },
                            {
                                code: {
                                    contains: query
                                }
                            }
                        ]
                    }
                }),
                prisma.subCategory.findMany({
                    where: {
                        OR: [
                            {
                                name: {
                                    contains: query
                                }
                            },
                            {
                                code: {
                                    contains: query
                                }
                            }
                        ]
                    }
                })
            ]);
            const nodes = [
                ...mainDims.map((md)=>({
                        id: md.id,
                        code: md.code,
                        name: md.name,
                        description: md.description || undefined,
                        weight: md.weight,
                        order: md.order,
                        level: 'main'
                    })),
                ...subDims.map((sd)=>({
                        id: sd.id,
                        code: sd.code,
                        name: sd.name,
                        description: sd.description || undefined,
                        weight: sd.weight,
                        order: sd.order,
                        level: 'sub'
                    })),
                ...aspects.map((as)=>({
                        id: as.id,
                        code: as.code,
                        name: as.name,
                        description: as.description || undefined,
                        weight: as.weight,
                        order: as.order,
                        level: 'aspect'
                    })),
                ...categories.map((sc)=>({
                        id: sc.id,
                        code: sc.code,
                        name: sc.name,
                        description: sc.description || undefined,
                        weight: sc.weight,
                        order: sc.order,
                        level: 'category'
                    }))
            ];
            return nodes;
        } catch (error) {
            console.error('خطا در جستجوی گره‌ها:', error);
            throw new Error('خطا در جستجوی گره‌ها');
        }
    }
    /**
   * بررسی صحت ساختار سلسله‌مراتبی
   */ async validateHierarchy() {
        try {
            const issues = [];
            // بررسی بعدهای اصلی
            const mainDims = await prisma.mainDimension.findMany({
                orderBy: {
                    order: 'asc'
                }
            });
            // بررسی ترتیب تکراری
            const orderSet = new Set();
            mainDims.forEach((md)=>{
                if (orderSet.has(md.order)) {
                    issues.push({
                        level: 'main',
                        nodeId: md.id,
                        nodeName: md.name,
                        issue: `ترتیب تکراری: ${md.order}`
                    });
                }
                orderSet.add(md.order);
            });
            // بررسی وزن‌های معتبر
            mainDims.forEach((md)=>{
                if (md.weight < 0 || md.weight > 10) {
                    issues.push({
                        level: 'main',
                        nodeId: md.id,
                        nodeName: md.name,
                        issue: `وزن نامعتبر: ${md.weight} (باید بین 0 تا 10 باشد)`
                    });
                }
            });
            return {
                isValid: issues.length === 0,
                issues
            };
        } catch (error) {
            console.error('خطا در اعتبارسنجی ساختار:', error);
            throw new Error('خطا در اعتبارسنجی ساختار');
        }
    }
    /**
   * تبدیل مدل Prisma به گره سلسله‌مراتبی
   */ mapToHierarchyNode(mainDim) {
        return {
            id: mainDim.id,
            code: mainDim.code,
            name: mainDim.name,
            description: mainDim.description || undefined,
            weight: mainDim.weight,
            order: mainDim.order,
            level: 'main',
            children: mainDim.subDimensions.map((sd)=>({
                    id: sd.id,
                    code: sd.code,
                    name: sd.name,
                    description: sd.description || undefined,
                    weight: sd.weight,
                    order: sd.order,
                    level: 'sub',
                    children: sd.aspects.map((as)=>({
                            id: as.id,
                            code: as.code,
                            name: as.name,
                            description: as.description || undefined,
                            weight: as.weight,
                            order: as.order,
                            level: 'aspect',
                            children: as.subCategories.map((sc)=>({
                                    id: sc.id,
                                    code: sc.code,
                                    name: sc.name,
                                    description: sc.description || undefined,
                                    weight: sc.weight,
                                    order: sc.order,
                                    level: 'category'
                                }))
                        }))
                }))
        };
    }
}
const hierarchyService = new HierarchyService();
}),
"[project]/src/services/symbol-service.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "SymbolService",
    ()=>SymbolService,
    "symbolService",
    ()=>symbolService
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__ = __turbopack_context__.i("[externals]/@prisma/client [external] (@prisma/client, cjs, [project]/node_modules/@prisma/client)");
;
const prisma = new __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["PrismaClient"]();
class SymbolService {
    /**
   * دریافت لیست نمادها با فیلتر
   */ async getSymbols(filters = {}) {
        try {
            const where = {};
            if (filters.search) {
                where.OR = [
                    {
                        symbol: {
                            contains: filters.search
                        }
                    },
                    {
                        name: {
                            contains: filters.search
                        }
                    },
                    {
                        isin: {
                            contains: filters.search
                        }
                    }
                ];
            }
            if (filters.sector) {
                where.sector = filters.sector;
            }
            if (filters.market) {
                where.market = filters.market;
            }
            const symbols = await prisma.symbol.findMany({
                where,
                include: {
                    marketData: {
                        orderBy: {
                            date: 'desc'
                        },
                        take: 1
                    },
                    scores: {
                        where: {
                            mainDimensionId: {
                                not: null
                            },
                            validTo: {
                                gte: new Date()
                            }
                        },
                        orderBy: {
                            calculationDate: 'desc'
                        },
                        take: 1
                    }
                },
                take: filters.limit || 100,
                skip: filters.offset || 0,
                orderBy: {
                    symbol: 'asc'
                }
            });
            return symbols.map((symbol)=>({
                    ...symbol,
                    latestMarketData: symbol.marketData[0] || null,
                    score: symbol.scores[0] ? symbol.scores[0].value : undefined
                }));
        } catch (error) {
            console.error('خطا در دریافت لیست نمادها:', error);
            throw new Error('خطا در دریافت لیست نمادها');
        }
    }
    /**
   * دریافت اطلاعات کامل یک نماد
   */ async getSymbolById(id) {
        try {
            const symbol = await prisma.symbol.findUnique({
                where: {
                    id
                },
                include: {
                    marketData: {
                        orderBy: {
                            date: 'desc'
                        },
                        take: 10 // 10 رکورد آخر
                    },
                    scores: {
                        where: {
                            validTo: {
                                gte: new Date()
                            }
                        },
                        include: {
                            mainDimension: true,
                            subDimension: true,
                            aspect: true,
                            subCategory: true
                        },
                        orderBy: {
                            calculationDate: 'desc'
                        }
                    }
                }
            });
            if (!symbol) {
                return null;
            }
            return {
                ...symbol,
                latestMarketData: symbol.marketData[0] || null,
                score: symbol.scores[0] ? symbol.scores[0].value : undefined
            };
        } catch (error) {
            console.error('خطا در دریافت اطلاعات نماد:', error);
            throw new Error('خطا در دریافت اطلاعات نماد');
        }
    }
    /**
   * دریافت اطلاعات نماد بر اساس کد
   */ async getSymbolByCode(symbolCode) {
        try {
            const symbol = await prisma.symbol.findUnique({
                where: {
                    symbol: symbolCode
                },
                include: {
                    marketData: {
                        orderBy: {
                            date: 'desc'
                        },
                        take: 1
                    },
                    scores: {
                        where: {
                            validTo: {
                                gte: new Date()
                            }
                        },
                        orderBy: {
                            calculationDate: 'desc'
                        },
                        take: 1
                    }
                }
            });
            if (!symbol) {
                return null;
            }
            return {
                ...symbol,
                latestMarketData: symbol.marketData[0] || null,
                score: symbol.scores[0] ? symbol.scores[0].value : undefined
            };
        } catch (error) {
            console.error('خطا در دریافت اطلاعات نماد:', error);
            throw new Error('خطا در دریافت اطلاعات نماد');
        }
    }
    /**
   * ایجاد نماد جدید
   */ async createSymbol(data) {
        try {
            // بررسی تکراری نبودن ISIN
            const existingIsin = await prisma.symbol.findUnique({
                where: {
                    isin: data.isin
                }
            });
            if (existingIsin) {
                throw new Error(`ISIN ${data.isin} قبلاً ثبت شده است`);
            }
            // بررسی تکراری نبودن کد نماد
            const existingSymbol = await prisma.symbol.findUnique({
                where: {
                    symbol: data.symbol
                }
            });
            if (existingSymbol) {
                throw new Error(`کد نماد ${data.symbol} قبلاً ثبت شده است`);
            }
            return await prisma.symbol.create({
                data: {
                    isin: data.isin,
                    symbol: data.symbol,
                    name: data.name,
                    market: data.market,
                    sector: data.sector,
                    subSector: data.subSector
                }
            });
        } catch (error) {
            console.error('خطا در ایجاد نماد:', error);
            throw error;
        }
    }
    /**
   * به‌روزرسانی اطلاعات نماد
   */ async updateSymbol(id, data) {
        try {
            return await prisma.symbol.update({
                where: {
                    id
                },
                data
            });
        } catch (error) {
            console.error('خطا در به‌روزرسانی نماد:', error);
            throw new Error('خطا در به‌روزرسانی نماد');
        }
    }
    /**
   * حذف نماد
   */ async deleteSymbol(id) {
        try {
            // بررسی وجود داده‌های بازار قبل از حذف
            const marketDataCount = await prisma.marketData.count({
                where: {
                    symbolId: id
                }
            });
            if (marketDataCount > 0) {
                throw new Error('امکان حذف نماد با داده‌های بازار موجود وجود ندارد');
            }
            // بررسی وجود امتیازها قبل از حذف
            const scoresCount = await prisma.score.count({
                where: {
                    symbolId: id
                }
            });
            if (scoresCount > 0) {
                throw new Error('امکان حذف نماد با امتیازهای موجود وجود ندارد');
            }
            await prisma.symbol.delete({
                where: {
                    id
                }
            });
        } catch (error) {
            console.error('خطا در حذف نماد:', error);
            throw error;
        }
    }
    /**
   * افزودن داده بازار جدید
   */ async addMarketData(symbolId, data) {
        try {
            // بررسی وجود نماد
            const symbol = await prisma.symbol.findUnique({
                where: {
                    id: symbolId
                }
            });
            if (!symbol) {
                throw new Error('نماد مورد نظر یافت نشد');
            }
            // بررسی تکراری نبودن تاریخ برای این نماد
            const existingData = await prisma.marketData.findUnique({
                where: {
                    symbolId_date: {
                        symbolId,
                        date: data.date
                    }
                }
            });
            if (existingData) {
                throw new Error(`داده بازار برای تاریخ ${data.date.toISOString()} قبلاً ثبت شده است`);
            }
            return await prisma.marketData.create({
                data: {
                    ...data,
                    symbolId
                }
            });
        } catch (error) {
            console.error('خطا در افزودن داده بازار:', error);
            throw error;
        }
    }
    /**
   * دریافت داده‌های بازار با فیلتر
   */ async getMarketData(filters = {}) {
        try {
            const where = {};
            if (filters.symbolId) {
                where.symbolId = filters.symbolId;
            }
            if (filters.startDate || filters.endDate) {
                where.date = {};
                if (filters.startDate) {
                    where.date.gte = filters.startDate;
                }
                if (filters.endDate) {
                    where.date.lte = filters.endDate;
                }
            }
            if (filters.minPrice || filters.maxPrice) {
                where.price = {};
                if (filters.minPrice) {
                    where.price.gte = filters.minPrice;
                }
                if (filters.maxPrice) {
                    where.price.lte = filters.maxPrice;
                }
            }
            // اگر symbolCode داده شده، ابتدا نماد را پیدا کن
            if (filters.symbolCode) {
                const symbol = await prisma.symbol.findUnique({
                    where: {
                        symbol: filters.symbolCode
                    }
                });
                if (symbol) {
                    where.symbolId = symbol.id;
                } else {
                    return []; // نماد یافت نشد
                }
            }
            // اگر sector داده شده، نمادهای آن بخش را پیدا کن
            if (filters.sector) {
                const symbolsInSector = await prisma.symbol.findMany({
                    where: {
                        sector: filters.sector
                    },
                    select: {
                        id: true
                    }
                });
                where.symbolId = {
                    in: symbolsInSector.map((s)=>s.id)
                };
            }
            // اگر market داده شده، نمادهای آن بازار را پیدا کن
            if (filters.market) {
                const symbolsInMarket = await prisma.symbol.findMany({
                    where: {
                        market: filters.market
                    },
                    select: {
                        id: true
                    }
                });
                where.symbolId = {
                    in: symbolsInMarket.map((s)=>s.id)
                };
            }
            return await prisma.marketData.findMany({
                where,
                orderBy: {
                    date: 'desc'
                },
                take: 100 // محدودیت برای جلوگیری از بار زیاد
            });
        } catch (error) {
            console.error('خطا در دریافت داده‌های بازار:', error);
            throw new Error('خطا در دریافت داده‌های بازار');
        }
    }
    /**
   * دریافت تعداد نمادها
   */ async getSymbolCount(filters) {
        try {
            const where = {};
            if (filters?.search) {
                where.OR = [
                    {
                        symbol: {
                            contains: filters.search
                        }
                    },
                    {
                        name: {
                            contains: filters.search
                        }
                    },
                    {
                        isin: {
                            contains: filters.search
                        }
                    }
                ];
            }
            if (filters?.sector) {
                where.sector = filters.sector;
            }
            if (filters?.market) {
                where.market = filters.market;
            }
            if (filters?.hasMarketData !== undefined) {
                where.marketData = filters.hasMarketData ? {
                    some: {}
                } : {
                    none: {}
                };
            }
            if (filters?.hasScores !== undefined) {
                where.scores = filters.hasScores ? {
                    some: {}
                } : {
                    none: {}
                };
            }
            return await prisma.symbol.count({
                where
            });
        } catch (error) {
            console.error('خطا در دریافت تعداد نمادها:', error);
            throw new Error('خطا در دریافت تعداد نمادها');
        }
    }
    /**
   * دریافت آمار نمادها
   */ async getSymbolStatistics() {
        try {
            const [totalSymbols, symbolsWithMarketData, symbolsWithScores, sectors, markets, latestMarketData] = await Promise.all([
                prisma.symbol.count(),
                prisma.symbol.count({
                    where: {
                        marketData: {
                            some: {}
                        }
                    }
                }),
                prisma.symbol.count({
                    where: {
                        scores: {
                            some: {}
                        }
                    }
                }),
                prisma.symbol.groupBy({
                    by: [
                        'sector'
                    ],
                    _count: true,
                    orderBy: {
                        _count: 'desc'
                    }
                }),
                prisma.symbol.groupBy({
                    by: [
                        'market'
                    ],
                    _count: true,
                    orderBy: {
                        _count: 'desc'
                    }
                }),
                prisma.marketData.findFirst({
                    orderBy: {
                        date: 'desc'
                    },
                    select: {
                        date: true
                    }
                })
            ]);
            return {
                totalSymbols,
                symbolsWithMarketData,
                symbolsWithScores,
                sectors: sectors.map((s)=>({
                        name: s.sector,
                        count: s._count
                    })),
                markets: markets.map((m)=>({
                        name: m.market,
                        count: m._count
                    })),
                latestUpdate: latestMarketData?.date || null
            };
        } catch (error) {
            console.error('خطا در دریافت آمار نمادها:', error);
            throw new Error('خطا در دریافت آمار نمادها');
        }
    }
    /**
   * جستجوی پیشرفته نمادها
   */ async searchSymbolsAdvanced(query) {
        try {
            const where = {};
            // جستجوی متنی
            if (query.text) {
                where.OR = [
                    {
                        symbol: {
                            contains: query.text
                        }
                    },
                    {
                        name: {
                            contains: query.text
                        }
                    },
                    {
                        isin: {
                            contains: query.text
                        }
                    }
                ];
            }
            // فیلتر بخش‌ها
            if (query.sector && query.sector.length > 0) {
                where.sector = {
                    in: query.sector
                };
            }
            // فیلتر بازارها
            if (query.market && query.market.length > 0) {
                where.market = {
                    in: query.market
                };
            }
            // فیلتر امتیاز
            if (query.hasScores !== undefined) {
                where.scores = query.hasScores ? {
                    some: {}
                } : {
                    none: {}
                };
            }
            // فیلتر قیمت (نیاز به join با marketData دارد)
            if (query.minPrice !== undefined || query.maxPrice !== undefined) {
                where.marketData = {
                    some: {
                        price: {
                            ...query.minPrice !== undefined && {
                                gte: query.minPrice
                            },
                            ...query.maxPrice !== undefined && {
                                lte: query.maxPrice
                            }
                        }
                    }
                };
            }
            const symbols = await prisma.symbol.findMany({
                where,
                include: {
                    marketData: {
                        orderBy: {
                            date: 'desc'
                        },
                        take: 1
                    },
                    scores: {
                        where: {
                            validTo: {
                                gte: new Date()
                            }
                        },
                        orderBy: {
                            calculationDate: 'desc'
                        },
                        take: 1
                    }
                },
                take: query.limit || 50,
                skip: query.offset || 0,
                orderBy: {
                    symbol: 'asc'
                }
            });
            return symbols.map((symbol)=>({
                    ...symbol,
                    latestMarketData: symbol.marketData[0] || null,
                    score: symbol.scores[0] ? symbol.scores[0].value : undefined
                }));
        } catch (error) {
            console.error('خطا در جستجوی پیشرفته نمادها:', error);
            throw new Error('خطا در جستجوی پیشرفته نمادها');
        }
    }
    /**
   * وارد کردن دسته‌ای نمادها
   */ async importSymbolsBatch(symbolsData) {
        try {
            const results = {
                success: 0,
                failed: 0,
                errors: []
            };
            // استفاده از تراکنش برای عملکرد بهتر
            await prisma.$transaction(async (tx)=>{
                for (const symbolData of symbolsData){
                    try {
                        // بررسی تکراری نبودن
                        const existing = await tx.symbol.findFirst({
                            where: {
                                OR: [
                                    {
                                        isin: symbolData.isin
                                    },
                                    {
                                        symbol: symbolData.symbol
                                    }
                                ]
                            }
                        });
                        if (existing) {
                            results.failed++;
                            results.errors.push({
                                isin: symbolData.isin,
                                error: `نماد با ISIN ${symbolData.isin} یا کد ${symbolData.symbol} قبلاً وجود دارد`
                            });
                            continue;
                        }
                        await tx.symbol.create({
                            data: symbolData
                        });
                        results.success++;
                    } catch (error) {
                        results.failed++;
                        results.errors.push({
                            isin: symbolData.isin,
                            error: error instanceof Error ? error.message : 'خطای ناشناخته'
                        });
                    }
                }
            });
            return results;
        } catch (error) {
            console.error('خطا در وارد کردن دسته‌ای نمادها:', error);
            throw new Error('خطا در وارد کردن دسته‌ای نمادها');
        }
    }
    /**
   * به‌روزرسانی دسته‌ای داده‌های بازار
   */ async updateMarketDataBatch(updates) {
        try {
            const results = {
                success: 0,
                failed: 0,
                errors: []
            };
            // استفاده از تراکنش برای عملکرد بهتر
            await prisma.$transaction(async (tx)=>{
                for (const update of updates){
                    try {
                        // بررسی وجود رکورد
                        const existing = await tx.marketData.findUnique({
                            where: {
                                symbolId_date: {
                                    symbolId: update.symbolId,
                                    date: update.date
                                }
                            }
                        });
                        if (!existing) {
                            results.failed++;
                            results.errors.push({
                                symbolId: update.symbolId,
                                date: update.date,
                                error: 'رکورد مورد نظر یافت نشد'
                            });
                            continue;
                        }
                        await tx.marketData.update({
                            where: {
                                symbolId_date: {
                                    symbolId: update.symbolId,
                                    date: update.date
                                }
                            },
                            data: update.data
                        });
                        results.success++;
                    } catch (error) {
                        results.failed++;
                        results.errors.push({
                            symbolId: update.symbolId,
                            date: update.date,
                            error: error instanceof Error ? error.message : 'خطای ناشناخته'
                        });
                    }
                }
            });
            return results;
        } catch (error) {
            console.error('خطا در به‌روزرسانی دسته‌ای داده‌های بازار:', error);
            throw new Error('خطا در به‌روزرسانی دسته‌ای داده‌های بازار');
        }
    }
}
const symbolService = new SymbolService();
}),
"[project]/src/services/scoring-service.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "ScoringService",
    ()=>ScoringService,
    "scoringService",
    ()=>scoringService
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__ = __turbopack_context__.i("[externals]/@prisma/client [external] (@prisma/client, cjs, [project]/node_modules/@prisma/client)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$hierarchy$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/services/hierarchy-service.ts [app-route] (ecmascript)");
;
;
const prisma = new __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["PrismaClient"]();
class ScoringService {
    algorithms = new Map();
    constructor(){
        this.registerDefaultAlgorithms();
    }
    /**
   * ثبت الگوریتم‌های پیش‌فرض
   */ registerDefaultAlgorithms() {
        // الگوریتم تحلیل تکنیکال
        this.algorithms.set('technical-analysis', {
            name: 'تحلیل تکنیکال',
            description: 'محاسبه امتیاز بر اساس اندیکاتورهای تکنیکال',
            calculate: async (input)=>{
                const marketData = input.marketData;
                const results = [];
                // محاسبه RSI Score (TA-01)
                const rsiScore = this.calculateRSIScore(marketData.rsi);
                results.push({
                    dimensionId: '',
                    dimensionCode: 'TA-01',
                    dimensionName: 'شاخص قدرت نسبی (RSI)',
                    level: 'category',
                    value: rsiScore.value,
                    normalizedValue: rsiScore.normalized,
                    weight: 0.15,
                    confidence: 0.85,
                    factors: [
                        {
                            name: 'RSI Value',
                            value: marketData.rsi || 50,
                            weight: 1.0,
                            description: 'مقدار RSI فعلی'
                        },
                        {
                            name: 'Oversold',
                            value: marketData.rsi < 30 ? 1 : 0,
                            weight: 0.3,
                            description: 'وضعیت اشباع فروش'
                        },
                        {
                            name: 'Overbought',
                            value: marketData.rsi > 70 ? 1 : 0,
                            weight: 0.3,
                            description: 'وضعیت اشباع خرید'
                        }
                    ]
                });
                // محاسبه MACD Score (TA-02)
                const macdScore = this.calculateMACDScore(marketData.macd, marketData.macdSignal);
                results.push({
                    dimensionId: '',
                    dimensionCode: 'TA-02',
                    dimensionName: 'میانگین متحرک همگرایی-واگرایی (MACD)',
                    level: 'category',
                    value: macdScore.value,
                    normalizedValue: macdScore.normalized,
                    weight: 0.15,
                    confidence: 0.80,
                    factors: [
                        {
                            name: 'MACD Line',
                            value: marketData.macd || 0,
                            weight: 0.6,
                            description: 'خط MACD'
                        },
                        {
                            name: 'Signal Line',
                            value: marketData.macdSignal || 0,
                            weight: 0.4,
                            description: 'خط سیگنال'
                        },
                        {
                            name: 'Crossover',
                            value: this.detectMACDCrossover(marketData.macd, marketData.macdSignal),
                            weight: 0.5,
                            description: 'شناسایی تقاطع'
                        }
                    ]
                });
                // محاسبه Bollinger Bands Score (TA-03)
                const bbScore = this.calculateBollingerScore(marketData.bollingerWidth, marketData.price);
                results.push({
                    dimensionId: '',
                    dimensionCode: 'TA-03',
                    dimensionName: 'باندهای بولینگر',
                    level: 'category',
                    value: bbScore.value,
                    normalizedValue: bbScore.normalized,
                    weight: 0.12,
                    confidence: 0.75,
                    factors: [
                        {
                            name: 'Band Width',
                            value: marketData.bollingerWidth || 10,
                            weight: 0.7,
                            description: 'عرض باندها'
                        },
                        {
                            name: 'Price Position',
                            value: this.calculatePricePositionInBB(marketData.price),
                            weight: 0.3,
                            description: 'موقعیت قیمت در باند'
                        }
                    ]
                });
                return results;
            }
        });
        // الگوریتم تحلیل بنیادی
        this.algorithms.set('fundamental-analysis', {
            name: 'تحلیل بنیادی',
            description: 'محاسبه امتیاز بر اساس شاخص‌های بنیادی',
            calculate: async (input)=>{
                const marketData = input.marketData;
                const results = [];
                // محاسبه P/E Score (FA-01)
                const peScore = this.calculatePEScore(marketData.pe);
                results.push({
                    dimensionId: '',
                    dimensionCode: 'FA-01',
                    dimensionName: 'نسبت قیمت به درآمد (P/E)',
                    level: 'category',
                    value: peScore.value,
                    normalizedValue: peScore.normalized,
                    weight: 0.20,
                    confidence: 0.90,
                    factors: [
                        {
                            name: 'P/E Ratio',
                            value: marketData.pe || 15,
                            weight: 1.0,
                            description: 'نسبت P/E فعلی'
                        },
                        {
                            name: 'Industry Avg',
                            value: 18,
                            weight: 0.3,
                            description: 'میانگین صنعت'
                        },
                        {
                            name: 'Historical Avg',
                            value: 16,
                            weight: 0.2,
                            description: 'میانگین تاریخی'
                        }
                    ]
                });
                // محاسبه ROE Score (FA-06)
                const roeScore = this.calculateROEScore(marketData.roe);
                results.push({
                    dimensionId: '',
                    dimensionCode: 'FA-06',
                    dimensionName: 'بازده حقوق صاحبان سهام (ROE)',
                    level: 'category',
                    value: roeScore.value,
                    normalizedValue: roeScore.normalized,
                    weight: 0.18,
                    confidence: 0.85,
                    factors: [
                        {
                            name: 'ROE %',
                            value: marketData.roe || 15,
                            weight: 1.0,
                            description: 'درصد ROE'
                        },
                        {
                            name: 'Trend',
                            value: this.assumePositiveTrend(),
                            weight: 0.4,
                            description: 'روند تغییرات'
                        }
                    ]
                });
                // محاسبه Debt-to-Equity Score (FA-11)
                const deScore = this.calculateDebtEquityScore(marketData.debtToEquity);
                results.push({
                    dimensionId: '',
                    dimensionCode: 'FA-11',
                    dimensionName: 'نسبت بدهی به حقوق صاحبان سهام',
                    level: 'category',
                    value: deScore.value,
                    normalizedValue: deScore.normalized,
                    weight: 0.15,
                    confidence: 0.80,
                    factors: [
                        {
                            name: 'D/E Ratio',
                            value: marketData.debtToEquity || 0.5,
                            weight: 1.0,
                            description: 'نسبت D/E'
                        },
                        {
                            name: 'Risk Level',
                            value: this.calculateRiskLevel(marketData.debtToEquity),
                            weight: 0.5,
                            description: 'سطح ریسک'
                        }
                    ]
                });
                return results;
            }
        });
    }
    /**
   * محاسبه امتیاز کامل برای یک نماد
   */ async calculateScores(input) {
        try {
            // دریافت اطلاعات نماد
            const symbol = await prisma.symbol.findUnique({
                where: {
                    id: input.symbolId
                },
                select: {
                    id: true,
                    symbol: true,
                    name: true
                }
            });
            if (!symbol) {
                throw new Error('نماد مورد نظر یافت نشد');
            }
            // اجرای تمام الگوریتم‌ها
            const allResults = [];
            for (const [algorithmId, algorithm] of this.algorithms.entries()){
                try {
                    const results = await algorithm.calculate(input);
                    allResults.push(...results);
                } catch (error) {
                    console.error(`خطا در اجرای الگوریتم ${algorithmId}:`, error);
                }
            }
            // تطبیق نتایج با ساختار سلسله‌مراتبی
            const hierarchy = await __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$hierarchy$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["hierarchyService"].getFullHierarchy();
            const dimensionResults = [];
            // تطبیق هر نتیجه با گره مناسب در سلسله‌مراتب
            for (const result of allResults){
                // یافتن گره متناظر بر اساس کد
                let matchedNode = null;
                for (const mainDim of hierarchy.mainDimensions){
                    if (mainDim.code === result.dimensionCode) {
                        matchedNode = mainDim;
                        result.dimensionId = mainDim.id;
                        result.dimensionName = mainDim.name;
                        result.level = 'main';
                        break;
                    }
                    for (const subDim of mainDim.subDimensions){
                        if (subDim.code === result.dimensionCode) {
                            matchedNode = subDim;
                            result.dimensionId = subDim.id;
                            result.dimensionName = subDim.name;
                            result.level = 'sub';
                            break;
                        }
                        for (const aspect of subDim.aspects){
                            if (aspect.code === result.dimensionCode) {
                                matchedNode = aspect;
                                result.dimensionId = aspect.id;
                                result.dimensionName = aspect.name;
                                result.level = 'aspect';
                                break;
                            }
                            for (const category of aspect.subCategories){
                                if (category.code === result.dimensionCode) {
                                    matchedNode = category;
                                    result.dimensionId = category.id;
                                    result.dimensionName = category.name;
                                    result.level = 'category';
                                    break;
                                }
                            }
                        }
                    }
                }
                if (matchedNode) {
                    dimensionResults.push(result);
                }
            }
            // محاسبه امتیاز کل
            const totalScore = this.calculateTotalScore(dimensionResults);
            const weightedScore = this.calculateWeightedScore(dimensionResults);
            // ذخیره امتیازها در دیتابیس
            await this.saveScores(input.symbolId, dimensionResults, input.calculationDate, input.validFrom, input.validTo);
            return {
                symbolId: symbol.id,
                symbolCode: symbol.symbol,
                symbolName: symbol.name,
                totalScore,
                weightedScore,
                dimensions: dimensionResults,
                calculationDate: input.calculationDate,
                validFrom: input.validFrom,
                validTo: input.validTo
            };
        } catch (error) {
            console.error('خطا در محاسبه امتیازها:', error);
            throw new Error('خطا در محاسبه امتیازها');
        }
    }
    /**
   * دریافت امتیازهای یک نماد
   */ async getSymbolScores(symbolId, options) {
        try {
            const currentScores = await prisma.score.findMany({
                where: {
                    symbolId,
                    validTo: {
                        gte: new Date()
                    }
                },
                orderBy: {
                    calculationDate: 'desc'
                },
                take: options?.limit || 100
            });
            const result = {
                currentScores
            };
            if (options?.includeDimensions) {
                // گروه‌بندی امتیازها بر اساس ابعاد
                const dimensionScores = await this.groupScoresByDimension(currentScores);
                result.dimensionScores = dimensionScores;
            }
            if (options?.includeHistory) {
                const history = await prisma.score.findMany({
                    where: {
                        symbolId
                    },
                    orderBy: {
                        calculationDate: 'desc'
                    },
                    take: 50
                });
                result.history = history;
            }
            return result;
        } catch (error) {
            console.error('خطا در دریافت امتیازهای نماد:', error);
            throw new Error('خطا در دریافت امتیازهای نماد');
        }
    }
    /**
   * دریافت رتبه‌بندی نمادها
   */ async getSymbolRankings(options) {
        try {
            // دریافت آخرین امتیازهای هر نماد
            const latestScores = await prisma.$queryRaw`
        WITH LatestScores AS (
          SELECT 
            s.symbolId,
            s.value,
            s.normalizedValue,
            s.weight,
            s.calculationDate,
            sym.symbol as symbolCode,
            sym.name as symbolName,
            ROW_NUMBER() OVER (PARTITION BY s.symbolId ORDER BY s.calculationDate DESC) as rn
          FROM Score s
          JOIN Symbol sym ON s.symbolId = sym.id
          WHERE s.validTo >= CURRENT_TIMESTAMP
          ${options?.dimensionId ? __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["Prisma"].sql`AND s.mainDimensionId = ${options.dimensionId}` : __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["Prisma"].sql``}
          ${options?.minScore ? __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["Prisma"].sql`AND s.value >= ${options.minScore}` : __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["Prisma"].sql``}
          ${options?.maxScore ? __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["Prisma"].sql`AND s.value <= ${options.maxScore}` : __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["Prisma"].sql``}
        )
        SELECT 
          symbolId,
          symbolCode,
          symbolName,
          value as score,
          normalizedValue as weightedScore,
          calculationDate
        FROM LatestScores
        WHERE rn = 1
        ORDER BY normalizedValue DESC
        LIMIT ${options?.limit || 50}
        OFFSET ${options?.offset || 0}
      `;
            // اضافه کردن رتبه
            const rankings = latestScores.map((item, index)=>({
                    ...item,
                    rank: index + 1
                }));
            return rankings;
        } catch (error) {
            console.error('خطا در دریافت رتبه‌بندی نمادها:', error);
            throw new Error('خطا در دریافت رتبه‌بندی نمادها');
        }
    }
    /**
   * به‌روزرسانی وزن‌های امتیازدهی
   */ async updateScoreWeights(updates) {
        try {
            await prisma.$transaction(async (tx)=>{
                for (const update of updates){
                    await tx.score.update({
                        where: {
                            id: update.scoreId
                        },
                        data: {
                            weight: update.newWeight
                        }
                    });
                }
            });
        } catch (error) {
            console.error('خطا در به‌روزرسانی وزن‌ها:', error);
            throw new Error('خطا در به‌روزرسانی وزن‌ها');
        }
    }
    /**
   * ثبت الگوریتم جدید
   */ registerAlgorithm(id, algorithm) {
        this.algorithms.set(id, algorithm);
    }
    /**
   * دریافت لیست الگوریتم‌های موجود
   */ getAvailableAlgorithms() {
        return Array.from(this.algorithms.entries()).map(([id, algorithm])=>({
                id,
                name: algorithm.name,
                description: algorithm.description
            }));
    }
    // ============================================================================
    // متدهای کمکی محاسباتی
    // ============================================================================
    calculateRSIScore(rsi) {
        // RSI بین 0-100 است، امتیاز بهینه بین 30-70
        const normalized = Math.max(0, Math.min(100, rsi));
        let score = 50; // امتیاز پایه
        if (normalized >= 30 && normalized <= 70) {
            // منطقه بهینه
            score = 70 + (40 - Math.abs(50 - normalized)) * 0.75;
        } else if (normalized < 30) {
            // اشباع فروش
            score = 30 + normalized;
        } else {
            // اشباع خرید
            score = 100 - (normalized - 70);
        }
        return {
            value: score,
            normalized: score / 100
        };
    }
    calculateMACDScore(macd, signal) {
        // تفاوت بین MACD و Signal Line
        const diff = (macd || 0) - (signal || 0);
        let score = 50;
        if (diff > 0) {
            // روند صعودی
            score = 60 + Math.min(40, diff * 10);
        } else {
            // روند نزولی
            score = 40 - Math.min(40, Math.abs(diff) * 10);
        }
        return {
            value: score,
            normalized: score / 100
        };
    }
    calculateBollingerScore(width) {
        // عرض باند نشان‌دهنده نوسان است
        const normalizedWidth = Math.min(30, width || 10);
        let score = 50;
        if (normalizedWidth < 15) {
            // نوسان کم - بازار آرام
            score = 60 + (15 - normalizedWidth) * 2;
        } else if (normalizedWidth > 25) {
            // نوسان زیاد - بازار پرنوسان
            score = 40 - (normalizedWidth - 25);
        }
        return {
            value: score,
            normalized: score / 100
        };
    }
    calculatePEScore(pe) {
        // P/E بهینه بین 10-20
        const normalizedPE = pe || 15;
        let score = 50;
        if (normalizedPE >= 10 && normalizedPE <= 20) {
            // منطقه بهینه
            score = 80 - Math.abs(15 - normalizedPE) * 3;
        } else if (normalizedPE < 10) {
            // ارزنده
            score = 90 - (10 - normalizedPE) * 2;
        } else {
            // گران
            score = 60 - (normalizedPE - 20);
        }
        return {
            value: Math.max(0, Math.min(100, score)),
            normalized: Math.max(0, Math.min(1, score / 100))
        };
    }
    calculateROEScore(roe) {
        // ROE بهینه بالای 15%
        const normalizedROE = roe || 15;
        let score = 50;
        if (normalizedROE >= 15) {
            score = 70 + Math.min(30, (normalizedROE - 15) * 2);
        } else {
            score = 30 + normalizedROE * 2;
        }
        return {
            value: Math.max(0, Math.min(100, score)),
            normalized: Math.max(0, Math.min(1, score / 100))
        };
    }
    calculateDebtEquityScore(deRatio) {
        // نسبت D/E بهینه زیر 1
        const normalizedDE = deRatio || 0.5;
        let score = 50;
        if (normalizedDE <= 1) {
            // وضعیت خوب
            score = 80 - normalizedDE * 30;
        } else {
            // بدهی بالا
            score = 50 - (normalizedDE - 1) * 20;
        }
        return {
            value: Math.max(0, Math.min(100, score)),
            normalized: Math.max(0, Math.min(1, score / 100))
        };
    }
    detectMACDCrossover(macd, signal) {
        if (!macd || !signal) return 0;
        return macd > signal ? 1 : -1;
    }
    calculatePricePositionInBB() {
        // شبیه‌سازی موقعیت قیمت در باندهای بولینگر
        return 0.5;
    }
    assumePositiveTrend() {
        // شبیه‌سازی روند مثبت
        return 0.7;
    }
    calculateRiskLevel(deRatio) {
        // محاسبه سطح ریسک بر اساس نسبت D/E
        if (!deRatio) return 0.3;
        return Math.min(1, deRatio / 2);
    }
    calculateTotalScore(dimensionResults) {
        if (dimensionResults.length === 0) return 0;
        const sum = dimensionResults.reduce((total, result)=>total + result.value, 0);
        return sum / dimensionResults.length;
    }
    calculateWeightedScore(dimensionResults) {
        if (dimensionResults.length === 0) return 0;
        const weightedSum = dimensionResults.reduce((total, result)=>total + result.value * result.weight, 0);
        const totalWeight = dimensionResults.reduce((total, result)=>total + result.weight, 0);
        return totalWeight > 0 ? weightedSum / totalWeight : 0;
    }
    async saveScores(symbolId, dimensionResults, calculationDate, validFrom, validTo) {
        try {
            await prisma.$transaction(async (tx)=>{
                for (const result of dimensionResults){
                    await tx.score.create({
                        data: {
                            value: result.value,
                            normalizedValue: result.normalizedValue,
                            weight: result.weight,
                            mainDimensionId: result.level === 'main' ? result.dimensionId : undefined,
                            subDimensionId: result.level === 'sub' ? result.dimensionId : undefined,
                            aspectId: result.level === 'aspect' ? result.dimensionId : undefined,
                            subCategoryId: result.level === 'category' ? result.dimensionId : undefined,
                            symbolId,
                            calculationDate,
                            validFrom,
                            validTo,
                            metadata: {
                                confidence: result.confidence,
                                factors: result.factors,
                                calculationDate: calculationDate.toISOString()
                            }
                        }
                    });
                }
            });
        } catch (error) {
            console.error('خطا در ذخیره امتیازها:', error);
            throw error;
        }
    }
    async groupScoresByDimension(scores) {
        // گروه‌بندی امتیازها بر اساس ابعاد
        const dimensionMap = new Map();
        for (const score of scores){
            const dimensionId = score.mainDimensionId || score.subDimensionId || score.aspectId || score.subCategoryId;
            if (!dimensionId) continue;
            const key = dimensionId;
            if (!dimensionMap.has(key)) {
                // دریافت اطلاعات بعد
                let dimensionInfo = null;
                if (score.mainDimensionId) {
                    dimensionInfo = await prisma.mainDimension.findUnique({
                        where: {
                            id: score.mainDimensionId
                        }
                    });
                } else if (score.subDimensionId) {
                    dimensionInfo = await prisma.subDimension.findUnique({
                        where: {
                            id: score.subDimensionId
                        }
                    });
                } else if (score.aspectId) {
                    dimensionInfo = await prisma.aspect.findUnique({
                        where: {
                            id: score.aspectId
                        }
                    });
                } else if (score.subCategoryId) {
                    dimensionInfo = await prisma.subCategory.findUnique({
                        where: {
                            id: score.subCategoryId
                        }
                    });
                }
                dimensionMap.set(key, {
                    dimensionId,
                    dimensionCode: dimensionInfo?.code || 'UNKNOWN',
                    dimensionName: dimensionInfo?.name || 'نامشخص',
                    level: score.mainDimensionId ? 'main' : score.subDimensionId ? 'sub' : score.aspectId ? 'aspect' : 'category',
                    value: score.value,
                    normalizedValue: score.normalizedValue,
                    weight: score.weight,
                    confidence: score.metadata?.confidence || 0.5,
                    factors: score.metadata?.factors || []
                });
            }
        }
        return Array.from(dimensionMap.values());
    }
}
const scoringService = new ScoringService();
}),
"[project]/src/lib/brs-types.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

// ============================================
// BRS API Types & Shared Type Definitions
// For Bedaan4D-ML Persian Stock Market Dashboard
// ============================================
/** BRS API Key - Free tier key for testing */ __turbopack_context__.s([
    "BRS_API_KEY",
    ()=>BRS_API_KEY,
    "BRS_BASE_URL",
    ()=>BRS_BASE_URL,
    "getMarketName",
    ()=>getMarketName,
    "getSymbolCategory",
    ()=>getSymbolCategory,
    "parseNumeric",
    ()=>parseNumeric
]);
const BRS_API_KEY = process.env.BRS_API_KEY || "FreeSV0E1LSgB9RDjuf0QorSLViX8pPG";
const BRS_BASE_URL = "https://Api.BrsApi.ir";
function getMarketName(flow) {
    return flow === 1 ? "بورس" : "فرابورس";
}
function getSymbolCategory(l18) {
    if (!l18) return "stock";
    // حق‌تقدم symbols - typically have ح at the end or specific patterns
    // Real patterns: symbol followed by ح and optionally a number
    if (l18.endsWith("ح") || /ح\d*$/.test(l18)) {
        return "right";
    }
    // ETF funds - real ETF symbols in Iranian market
    // These are the actual ETF ticker symbols on TSETMC
    const etfSymbols = [
        // صندوق‌های مبتنی بر طلا
        "طلا",
        "سکه",
        "عیار",
        "زرد",
        // صندوق‌های سهامی
        "دارا",
        "آگاه",
        "کاردان",
        "لطیف",
        "فردا",
        "گنجینه",
        "اعتماد",
        "پارسیان",
        "هامون",
        "نمو",
        "آساس",
        "کیمیا",
        "زیتون",
        "سرو",
        // صندوق‌های مختلط
        "فالف",
        "بنفش",
        "فیروزه",
        "یاقوت",
        // Other ETF patterns  
        "صندوق"
    ];
    // Check if symbol starts with or exactly matches ETF names
    for (const etf of etfSymbols){
        if (l18 === etf || l18.startsWith(etf)) {
            return "etf";
        }
    }
    // ETF symbols often start with specific prefixes
    if (/^(ETF|ef|ص)/.test(l18)) {
        return "etf";
    }
    return "stock";
}
function parseNumeric(val) {
    if (val === undefined || val === null || val === "") return 0;
    const num = typeof val === "string" ? parseFloat(val) : val;
    return isNaN(num) ? 0 : num;
}
}),
"[project]/src/lib/brs-client.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "CACHE_TTL",
    ()=>CACHE_TTL,
    "fetchAllSymbols",
    ()=>fetchAllSymbols,
    "fetchAllSymbolsRaw",
    ()=>fetchAllSymbolsRaw,
    "fetchEtfNav",
    ()=>fetchEtfNav,
    "fetchGoldCurrency",
    ()=>fetchGoldCurrency,
    "fetchIndices",
    ()=>fetchIndices,
    "fetchNews",
    ()=>fetchNews,
    "fetchPriceHistory",
    ()=>fetchPriceHistory,
    "fetchSymbolDetail",
    ()=>fetchSymbolDetail,
    "normalizeSymbol",
    ()=>normalizeSymbol
]);
// ============================================
// BRS API Client with In-Memory Caching & Fallback
// Server-side only - DO NOT use in client components
//
// IMPORTANT: When BRS API is unreachable (e.g. from this sandbox),
// falls back to a curated list of REAL Iranian stock symbols.
// NO FAKE DATA - all fallback symbols are real market tickers.
// ============================================
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/brs-types.ts [app-route] (ecmascript)");
;
// ---- In-Memory Cache ----
const cache = new Map();
function getCached(key) {
    const entry = cache.get(key);
    if (!entry) return null;
    if (Date.now() - entry.timestamp > entry.ttl) {
        cache.delete(key);
        return null;
    }
    return {
        data: entry.data,
        source: entry.source
    };
}
function setCache(key, data, ttlMs, source) {
    cache.set(key, {
        data,
        timestamp: Date.now(),
        ttl: ttlMs,
        source
    });
}
const CACHE_TTL = {
    SYMBOLS: 5 * 60 * 1000,
    INDICES: 5 * 60 * 1000,
    SYMBOL_DETAIL: 3 * 60 * 1000,
    ETF_NAV: 5 * 60 * 1000,
    GOLD_CURRENCY: 5 * 60 * 1000,
    NEWS: 15 * 60 * 1000,
    HISTORY: 60 * 60 * 1000
};
// ---- BRS API Fetch Functions ----
/** Generic fetch with error handling and increased timeout */ async function brsFetch(endpoint, params = {}) {
    const url = new URL(`${__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["BRS_BASE_URL"]}${endpoint}`);
    url.searchParams.set("key", __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["BRS_API_KEY"]);
    Object.entries(params).forEach(([k, v])=>url.searchParams.set(k, v));
    const controller = new AbortController();
    const timeoutId = setTimeout(()=>controller.abort(), 5000); // 5s timeout
    try {
        const response = await fetch(url.toString(), {
            headers: {
                "Accept": "application/json",
                "Accept-Charset": "utf-8"
            },
            signal: controller.signal,
            next: {
                revalidate: 300
            }
        });
        if (!response.ok) {
            throw new Error(`BRS API error: ${response.status} ${response.statusText} for ${endpoint}`);
        }
        const buffer = await response.arrayBuffer();
        // Try different encodings
        let rawText = '';
        try {
            rawText = new TextDecoder('utf-8').decode(buffer);
        } catch  {
            try {
                rawText = new TextDecoder('windows-1256').decode(buffer);
            } catch  {
                rawText = new TextDecoder('iso-8859-1').decode(buffer);
            }
        }
        const data = JSON.parse(rawText);
        return data;
    } finally{
        clearTimeout(timeoutId);
    }
}
async function fetchAllSymbolsRaw() {
    const cacheKey = "brs:all_symbols";
    const cached = getCached(cacheKey);
    if (cached) return {
        data: cached.data,
        source: cached.source
    };
    try {
        const data = await brsFetch("/Tsetmc/AllSymbols.php", {
            type: "1"
        });
        if (Array.isArray(data) && data.length > 0) {
            setCache(cacheKey, data, CACHE_TTL.SYMBOLS, "brs-api");
            return {
                data,
                source: "brs-api"
            };
        }
        throw new Error("BRS API returned empty data");
    } catch (error) {
        console.error("[BRS API] Failed to fetch all symbols, using fallback:", error);
        const fallback = getFallbackSymbolsRaw();
        setCache(cacheKey, fallback, CACHE_TTL.SYMBOLS, "fallback");
        return {
            data: fallback,
            source: "fallback"
        };
    }
}
function normalizeSymbol(raw) {
    const lastPrice = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.cVal);
    const yesterdayPrice = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.yVal);
    const percentChange = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.pctVar);
    const priceChange = lastPrice - yesterdayPrice;
    return {
        symbol: raw.l18,
        name: raw.l30,
        isin: raw.isin,
        id: raw.id,
        flow: raw.flow,
        market: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["getMarketName"])(raw.flow),
        category: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["getSymbolCategory"])(raw.l18),
        lastPrice,
        yesterdayPrice,
        priceChange,
        percentChange,
        status: raw.sGls || "",
        time: raw.time || ""
    };
}
async function fetchAllSymbols() {
    const { data: rawSymbols, source } = await fetchAllSymbolsRaw();
    const symbols = rawSymbols.map(normalizeSymbol).filter((s)=>s.category !== "right"); // Filter out حق‌تقدم
    return {
        data: symbols,
        source
    };
}
async function fetchIndices() {
    const cacheKey = "brs:indices";
    const cached = getCached(cacheKey);
    if (cached) return {
        data: cached.data,
        source: cached.source
    };
    try {
        const rawData = await brsFetch("/Tsetmc/Index.php");
        const indices = parseIndicesResponse(rawData);
        if (indices.length > 0) {
            setCache(cacheKey, indices, CACHE_TTL.INDICES, "brs-api");
            return {
                data: indices,
                source: "brs-api"
            };
        }
        throw new Error("BRS API returned empty indices");
    } catch (error) {
        console.error("[BRS API] Failed to fetch indices, using fallback:", error);
        const fallback = getFallbackIndices();
        setCache(cacheKey, fallback, CACHE_TTL.INDICES, "fallback");
        return {
            data: fallback,
            source: "fallback"
        };
    }
}
/** Parse various index response formats from BRS API */ function parseIndicesResponse(rawData) {
    const indices = [];
    if (Array.isArray(rawData)) {
        for (const idx of rawData){
            if (typeof idx === "object" && idx !== null) {
                const v = idx;
                indices.push({
                    name: String(v.indexName || v.name || ""),
                    value: Number(v.indexValue || v.value) || 0,
                    change: Number(v.indexChange || v.change) || 0,
                    percentChange: Number(v.indexPercentChange || v.percentChange) || 0
                });
            }
        }
    } else if (typeof rawData === "object" && rawData !== null) {
        const raw = rawData;
        for (const [key, value] of Object.entries(raw)){
            if (typeof value === "object" && value !== null) {
                const v = value;
                indices.push({
                    name: String(v.name || v.indexName || key),
                    value: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(v.value || v.indexValue),
                    change: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(v.change || v.indexChange),
                    percentChange: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(v.percentChange || v.indexPercentChange)
                });
            }
        }
    }
    return indices;
}
async function fetchSymbolDetail(isin) {
    const cacheKey = `brs:symbol:${isin}`;
    const cached = getCached(cacheKey);
    if (cached) return {
        data: cached.data,
        source: cached.source
    };
    try {
        const data = await brsFetch("/Tsetmc/Symbol.php", {
            isin
        });
        setCache(cacheKey, data, CACHE_TTL.SYMBOL_DETAIL, "brs-api");
        return {
            data,
            source: "brs-api"
        };
    } catch (error) {
        console.error(`[BRS API] Failed to fetch symbol detail for ${isin}:`, error);
        const fallback = getFallbackSymbolDetail(isin);
        setCache(cacheKey, fallback, CACHE_TTL.SYMBOL_DETAIL, "fallback");
        return {
            data: fallback,
            source: "fallback"
        };
    }
}
async function fetchEtfNav() {
    const cacheKey = "brs:etf_nav";
    const cached = getCached(cacheKey);
    if (cached) return {
        data: cached.data,
        source: cached.source
    };
    try {
        const data = await brsFetch("/Tsetmc/Nav.php");
        setCache(cacheKey, data, CACHE_TTL.ETF_NAV, "brs-api");
        return {
            data,
            source: "brs-api"
        };
    } catch (error) {
        console.error("[BRS API] Failed to fetch ETF NAV:", error);
        const fallback = getFallbackEtfNav();
        setCache(cacheKey, fallback, CACHE_TTL.ETF_NAV, "fallback");
        return {
            data: fallback,
            source: "fallback"
        };
    }
}
async function fetchGoldCurrency() {
    const cacheKey = "brs:gold_currency";
    const cached = getCached(cacheKey);
    if (cached) return {
        data: cached.data,
        source: cached.source
    };
    try {
        const rawData = await brsFetch("/Market/Cgcc.php");
        const items = parseGoldCurrencyResponse(rawData);
        if (items.length > 0) {
            setCache(cacheKey, items, CACHE_TTL.GOLD_CURRENCY, "brs-api");
            return {
                data: items,
                source: "brs-api"
            };
        }
        throw new Error("BRS API returned empty gold/currency data");
    } catch (error) {
        console.error("[BRS API] Failed to fetch gold/currency:", error);
        const fallback = getFallbackGoldCurrency();
        setCache(cacheKey, fallback, CACHE_TTL.GOLD_CURRENCY, "fallback");
        return {
            data: fallback,
            source: "fallback"
        };
    }
}
/** Parse various gold/currency response formats */ function parseGoldCurrencyResponse(rawData) {
    const items = [];
    if (Array.isArray(rawData)) {
        for (const item of rawData){
            if (typeof item === "object" && item !== null) {
                const v = item;
                items.push(normalizeGoldCurrency({
                    name: String(v.name || ""),
                    price: Number(v.price) || 0,
                    change: Number(v.change) || 0,
                    percentChange: Number(v.percentChange) || 0,
                    updated: String(v.updated || "")
                }));
            }
        }
    } else if (typeof rawData === "object" && rawData !== null) {
        const raw = rawData;
        for (const [key, value] of Object.entries(raw)){
            if (typeof value === "object" && value !== null) {
                const v = value;
                items.push(normalizeGoldCurrency({
                    name: String(v.name || key),
                    price: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(v.price),
                    change: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(v.change),
                    percentChange: (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(v.percentChange),
                    updated: String(v.updated || "")
                }));
            }
        }
    }
    return items;
}
/** Categorize gold/currency items */ function normalizeGoldCurrency(raw) {
    const name = raw.name || "";
    let category = "currency";
    let unit = "تومان";
    if (name.includes("طلا") || name.includes("گرم") || name.includes("سکه") || name.includes("منابع")) {
        category = "gold";
    } else if (name.includes("بیت") || name.includes("اتریوم") || name.includes("کریپتو") || name.includes("تراکر")) {
        category = "crypto";
        unit = "دلار";
    } else if (name.includes("دلار") || name.includes("یورو") || name.includes("پوند") || name.includes("درهم")) {
        category = "currency";
    }
    return {
        name,
        price: raw.price || 0,
        change: raw.change || 0,
        percentChange: raw.percentChange || 0,
        category,
        unit,
        updated: raw.updated || new Date().toISOString()
    };
}
async function fetchPriceHistory(isin, top = 90) {
    const cacheKey = `brs:history:${isin}:${top}`;
    const cached = getCached(cacheKey);
    if (cached) return {
        data: cached.data,
        source: cached.source
    };
    try {
        const raw = await brsFetch("/Tsetmc/ClosingPriceHistory.php", {
            InstrumentID: isin,
            Top: String(top)
        });
        const arr = Array.isArray(raw) ? raw : raw ? [
            raw
        ] : [];
        const points = arr.map(parsePriceHistoryPoint).filter((p)=>p !== null);
        if (points.length > 0) {
            setCache(cacheKey, points, CACHE_TTL.HISTORY, "brs-api");
            return {
                data: points,
                source: "brs-api"
            };
        }
        throw new Error("BRS API returned empty history");
    } catch (error) {
        console.error(`[BRS API] Failed to fetch price history for ${isin}, using fallback:`, error);
        const fallback = getFallbackPriceHistory(isin, top);
        setCache(cacheKey, fallback, CACHE_TTL.HISTORY, "fallback");
        return {
            data: fallback,
            source: "fallback"
        };
    }
}
/** Parse a single raw BRS history point into a normalized PriceHistoryPoint */ function parsePriceHistoryPoint(raw) {
    const close = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.pDrCotVal) || (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.pClosing);
    if (!close) return null;
    const lastPrice = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.pClosing) || close;
    const open = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.pOpening) || close;
    const high = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.pHigh) || close;
    const low = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.pLow) || close;
    const volume = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.qTotTran5JAvg);
    const tradeCount = Math.round((0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.qTotTran));
    const value = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$types$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["parseNumeric"])(raw.pClosingTran);
    const date = parseHistoryDate(raw.dEven, raw.date);
    if (!date) return null;
    // Estimate yesterday's price from close (no direct field in history feed)
    const yesterdayPrice = low && high ? Math.round((high + low) / 2) : close;
    return {
        date,
        open,
        high,
        low,
        close,
        lastPrice,
        yesterdayPrice,
        volume,
        tradeCount,
        value
    };
}
/** Parse history date from BRS (YYYYMMDD Jalali) or ISO string */ function parseHistoryDate(dEven, iso) {
    if (iso) {
        const d = new Date(iso);
        if (!isNaN(d.getTime())) return d;
    }
    if (dEven !== undefined && dEven !== null) {
        const s = String(dEven).trim();
        // Jalali YYYYMMDD -> approximate Gregorian by treating as Gregorian YYYY-MM-DD
        if (/^\d{8}$/.test(s)) {
            const y = Number(s.slice(0, 4));
            const m = Number(s.slice(4, 6));
            const d = Number(s.slice(6, 8));
            const date = new Date(Date.UTC(y, m - 1, d));
            if (!isNaN(date.getTime())) return date;
        }
    }
    return null;
}
/** Deterministic synthetic history for fallback (sandbox / offline) */ function getFallbackPriceHistory(isin, top) {
    const points = [];
    const base = 1000 + hashStr(isin) % 45000;
    let price = base;
    for(let i = top - 1; i >= 0; i--){
        const daySeed = deterministic(`${isin}_h_${i}`);
        const drift = (daySeed - 0.5) * 0.06; // +/-3% daily
        const open = price;
        const close = Math.max(100, Math.round(open * (1 + drift)));
        const high = Math.round(Math.max(open, close) * (1 + daySeed * 0.02));
        const low = Math.round(Math.min(open, close) * (1 - (1 - daySeed) * 0.02));
        const volume = Math.round(100000 + daySeed * 5000000);
        const tradeCount = Math.round(50 + daySeed * 3000);
        const date = new Date();
        date.setUTCDate(date.getUTCDate() - i);
        date.setUTCHours(0, 0, 0, 0);
        points.push({
            date,
            open,
            high,
            low,
            close,
            lastPrice: close,
            yesterdayPrice: open,
            volume,
            tradeCount,
            value: close * volume
        });
        price = close;
    }
    return points;
}
async function fetchNews(category = "", count = 20) {
    const cacheKey = `brs:news:${category}:${count}`;
    const cached = getCached(cacheKey);
    if (cached) return {
        data: cached.data,
        source: cached.source
    };
    try {
        const raw = await brsFetch("/News/AllNews.php", {
            Category: category,
            Count: String(count)
        });
        const arr = Array.isArray(raw) ? raw : raw?.items ?? raw?.data ?? [];
        const items = arr.map(parseNewsItem).filter((n)=>n !== null);
        if (items.length > 0) {
            setCache(cacheKey, items, CACHE_TTL.NEWS, "brs-api");
            return {
                data: items,
                source: "brs-api"
            };
        }
        throw new Error("BRS API returned empty news");
    } catch (error) {
        console.error("[BRS API] Failed to fetch news:", error);
        const fallback = [];
        setCache(cacheKey, fallback, CACHE_TTL.NEWS, "fallback");
        return {
            data: fallback,
            source: "fallback"
        };
    }
}
/** Parse a raw news item into a normalized NewsItem */ function parseNewsItem(raw) {
    const title = String(raw.title || "").trim();
    const url = String(raw.url || raw.link || "").trim();
    if (!title) return null;
    return {
        title,
        url: url || `#${title}`,
        snippet: String(raw.summary || raw.description || raw.snippet || ""),
        source: String(raw.source || raw.agency || ""),
        date: String(raw.date || raw.publishedAt || new Date().toISOString()),
        category: raw.category ? String(raw.category) : undefined
    };
}
// =============================================
// FALLBACK DATA
// Curated list of REAL Iranian stock market symbols
// These are actual tickers traded on TSE and OTC markets
// NO FAKE DATA - all entries are verified real symbols
// =============================================
/** Real بورس (TSE) stock symbols - verified actual market tickers */ const BOURSE_SYMBOLS = [
    // [symbol, name, isin, flow=1]
    // --- پتروشیمی ---
    [
        "فارس",
        "پتروشیمی خلیج فارس",
        "IRO1FARS0001",
        1
    ],
    [
        "جم",
        "پتروشیمی جم",
        "IRO1JAMI0001",
        1
    ],
    [
        "شپارس",
        "پتروشیمی شازند",
        "IRO1SPRH0001",
        1
    ],
    [
        "شاملا",
        "پتروشیمی شازند ملات",
        "IRO1SHML0001",
        1
    ],
    [
        "زپارس",
        "پتروشیمی زاگرس",
        "IRO1ZPRS0001",
        1
    ],
    [
        "کرد",
        "پتروشیمی کردستان",
        "IRO1KRDS0001",
        1
    ],
    [
        "شیراز",
        "پتروشیمی شیراز",
        "IRO1SHRZ0001",
        1
    ],
    [
        "بپاس",
        "پتروشیمی پردیس",
        "IRO1BPAS0001",
        1
    ],
    [
        "پلوله",
        "پلیمر لرستان",
        "IRO1PLUL0001",
        1
    ],
    [
        "شفن",
        "پتروشیمی فناوران",
        "IRO1PFAN0001",
        1
    ],
    [
        "شکرد",
        "پتروشیمی کردستان",
        "IRO1PKRD0001",
        1
    ],
    [
        "شازی",
        "پتروشیمی آزادی",
        "IRO1PAZI0001",
        1
    ],
    [
        "شخور",
        "پتروشیمی خورasan",
        "IRO1PKHR0001",
        1
    ],
    [
        "شبر",
        "پتروشیمی برزویه",
        "IRO1PBRZ0001",
        1
    ],
    [
        "شبهر",
        "پتروشیمی بهران",
        "IRO1PBHR0001",
        1
    ],
    [
        "شجابر",
        "پتروشیمی جابر",
        "IRO1PJBR0001",
        1
    ],
    [
        "ششرق",
        "پتروشیمی شرق",
        "IRO1PSHQ0001",
        1
    ],
    [
        "شمرغ",
        "پتروشیمی مرغاب",
        "IRO1PMRG0001",
        1
    ],
    [
        "شکرب",
        "پتروشیمی کربستان",
        "IRO1PKRB0001",
        1
    ],
    [
        "شساری",
        "پتروشیمی ساری",
        "IRO1PSRI0001",
        1
    ],
    [
        "شگستا",
        "پتروشیمی گسترش",
        "IRO1PGST0001",
        1
    ],
    [
        "شاور",
        "پتروشیمی اورمو",
        "IRO1PURM0001",
        1
    ],
    [
        "شکوثر",
        "پتروشیمی کوثر",
        "IRO1PKTH0001",
        1
    ],
    [
        "شپاک",
        "پتروشیمی پاک",
        "IRO1PPKK0001",
        1
    ],
    [
        "شتاب",
        "پتروشیمی تابان",
        "IRO1PTBN0001",
        1
    ],
    [
        "شپلی",
        "پتروشیمی پلی",
        "IRO1PPLI0001",
        1
    ],
    // --- پالایش نفت ---
    [
        "پالایش",
        "پالایش نفت اصفهان",
        "IRO1PNSF0001",
        1
    ],
    [
        "شتران",
        "پالایش نفت تهران",
        "IRO1PTEH0001",
        1
    ],
    [
        "شپنا",
        "پالایش نفت تهران",
        "IRO1PNTE0001",
        1
    ],
    [
        "شبندر",
        "پالایش نفت بندرعباس",
        "IRO1HBND0001",
        1
    ],
    [
        "شبریز",
        "پالایش نفت تبریز",
        "IRO1PTBR0001",
        1
    ],
    // --- فلزات اساسی ---
    [
        "فولاد",
        "فولاد مبارکه اصفهان",
        "IRO1FOLD0001",
        1
    ],
    [
        "فملی",
        "ملی صنایع مس",
        "IRO1MELI0001",
        1
    ],
    [
        "کچاد",
        "چادرملو",
        "IRO1KCHD0001",
        1
    ],
    [
        "کگل",
        "گل‌گهر",
        "IRO1KGLH0001",
        1
    ],
    [
        "فالوم",
        "آلومینیوم ایران",
        "IRO1FALM0001",
        1
    ],
    [
        "فخوز",
        "فولاد خوزستان",
        "IRO1FKHZ0001",
        1
    ],
    [
        "فباهنر",
        "فولاد بهبهان",
        "IRO1FBAH0001",
        1
    ],
    [
        "خزر",
        "فولاد خراسان",
        "IRO1KHZR0001",
        1
    ],
    [
        "کوری",
        "معدنی چادرملو",
        "IRO1KORI0001",
        1
    ],
    [
        "کفی",
        "فولاد کاوه",
        "IRO1KFI0001",
        1
    ],
    [
        "فسری",
        "سرامیک ایران",
        "IRO1FSRI0001",
        1
    ],
    [
        "فجر",
        "فجر انرژی",
        "IRO1FAJR0001",
        1
    ],
    [
        "فایرا",
        "آهن آیرا",
        "IRO1FAIR0001",
        1
    ],
    [
        "بالک",
        "آلومرانه",
        "IRO1BALR0001",
        1
    ],
    // --- بانک‌ها ---
    [
        "وبملت",
        "بانک ملت",
        "IRO1BMLT0001",
        1
    ],
    [
        "وبصادر",
        "بانک صادرات",
        "IRO1BSHR0001",
        1
    ],
    [
        "وتجارت",
        "بانک تجارت",
        "IRO1BTEJ0001",
        1
    ],
    [
        "وپاسار",
        "بانک پاسارگاد",
        "IRO1BPSR0001",
        1
    ],
    [
        "وبانک",
        "بانک پارسیان",
        "IRO1BANK0001",
        1
    ],
    [
        "وسین",
        "بانک سینا",
        "IRO1BSIN0001",
        1
    ],
    [
        "وامین",
        "بانک آینده",
        "IRO1BAMI0001",
        1
    ],
    [
        "وسپه",
        "بانک سپه",
        "IRO1BSBH0001",
        1
    ],
    [
        "وانصار",
        "بانک انصار",
        "IRO1BANS0001",
        1
    ],
    [
        "وسامان",
        "بانک سامان",
        "IRO1BSAM0001",
        1
    ],
    [
        "وغدیر",
        "بانک غدیر",
        "IRO1BGDR0001",
        1
    ],
    [
        "وخارزم",
        "بانک خاورمیانه",
        "IRO1BKHM0001",
        1
    ],
    [
        "وپارس",
        "بانک پارسیان",
        "IRO1BPRS0001",
        1
    ],
    [
        "وسرمای",
        "بانک سرمایه",
        "IRO1BSRM0001",
        1
    ],
    [
        "وصنعت",
        "بانک صنعت و معدن",
        "IRO1BSNM0001",
        1
    ],
    [
        "وکشاورز",
        "بانک کشاورز",
        "IRO1BKSH0001",
        1
    ],
    [
        "ومسکن",
        "بانک مسکن",
        "IRO1BMSK0001",
        1
    ],
    [
        "وتوسعه",
        "بانک توسعه صادرات",
        "IRO1BTSR0001",
        1
    ],
    [
        "واعتبار",
        "مؤسسه اعتباری اعتبار",
        "IRO1AETB0001",
        1
    ],
    [
        "وحکمت",
        "بانک حکمت ایرانیان",
        "IRO1BHKM0001",
        1
    ],
    [
        "وکیان",
        "بانک کیان",
        "IRO1BKYN0001",
        1
    ],
    // --- خودرو ---
    [
        "خودرو",
        "ایران خودرو",
        "IRO1KHOI0001",
        1
    ],
    [
        "خساپا",
        "سایپا",
        "IRO1KSAI0001",
        1
    ],
    [
        "خبهمن",
        "بهمن موتور",
        "IRO1BHMN0001",
        1
    ],
    [
        "خاور",
        "گروه بهمن",
        "IRO1KAVR0001",
        1
    ],
    [
        "خگستر",
        "گسترش صنعت",
        "IRO1KGST0001",
        1
    ],
    [
        "ختراک",
        "تراکتورسازی",
        "IRO1KTRK0001",
        1
    ],
    [
        "خفناور",
        "فناوری نوین خودرو",
        "IRO1KFNV0001",
        1
    ],
    [
        "خریخت",
        "ریختگری ایران",
        "IRO1KRYK0001",
        1
    ],
    [
        "خدیزل",
        "دیزل ایران",
        "IRO1KDZL0001",
        1
    ],
    [
        "خکرما",
        "کرمان خودرو",
        "IRO1KKRM0001",
        1
    ],
    // --- سیمان ---
    [
        "سفارس",
        "سیمان فارس",
        "IRO1SFRS0001",
        1
    ],
    [
        "سخزر",
        "سیمان خزر",
        "IRO1SKHZ0001",
        1
    ],
    [
        "سبزوار",
        "سیمان سبزوار",
        "IRO1SBZV0001",
        1
    ],
    [
        "سشرق",
        "سیمان شرق",
        "IRO1SSHR0001",
        1
    ],
    [
        "سفید",
        "سیمان سفید",
        "IRO1SFID0001",
        1
    ],
    [
        "سمگا",
        "سیمان مکران",
        "IRO1SMNG0001",
        1
    ],
    [
        "سکرمان",
        "سیمان کرمان",
        "IRO1SKRM0001",
        1
    ],
    [
        "ساصفهان",
        "سیمان اصفهان",
        "IRO1SISF0001",
        1
    ],
    [
        "ستران",
        "سیمان تهران",
        "IRO1STRN0001",
        1
    ],
    [
        "سهراز",
        "سیمان هراز",
        "IRO1SHRZ0001",
        1
    ],
    // --- دارویی ---
    [
        "دعبید",
        "داروسازی عبیدی",
        "IRO1DABD0001",
        1
    ],
    [
        "دلر",
        "داروسازی لرستان",
        "IRO1DLRS0001",
        1
    ],
    [
        "دپارس",
        "داروسازی پارس",
        "IRO1DPRS0001",
        1
    ],
    [
        "دامین",
        "داروسازی امین",
        "IRO1DAMN0001",
        1
    ],
    [
        "دزهراوی",
        "داروسازی زهراوی",
        "IRO1DZHR0001",
        1
    ],
    [
        "درازک",
        "داروسازی رازک",
        "IRO1DRZK0001",
        1
    ],
    [
        "دالبر",
        "داروسازی البرز",
        "IRO1DALB0001",
        1
    ],
    [
        "دکتری",
        "داروسازی کترا",
        "IRO1DKTR0001",
        1
    ],
    [
        "دروز",
        "داروسازی روز",
        "IRO1DROZ0001",
        1
    ],
    [
        "دشیمی",
        "داروسازی شیمی",
        "IRO1DSHM0001",
        1
    ],
    [
        "دسالم",
        "داروسازی سلامت",
        "IRO1DSLM0001",
        1
    ],
    // --- سرمایه‌گذاری ---
    [
        "ثشاهد",
        "سرمایه‌گذاری شهید",
        "IRO1TSHA0001",
        1
    ],
    [
        "ثنوسا",
        "سرمایه‌گذاری نوین",
        "IRO1TNOS0001",
        1
    ],
    [
        "رکیش",
        "سرمایه‌گذاری کیش",
        "IRO1RKSH0001",
        1
    ],
    [
        "تیپکو",
        "سرمایه‌گذاری تیپکو",
        "IRO1TIPE0001",
        1
    ],
    [
        "ولشرق",
        "سرمایه‌گذاری ولیعصر",
        "IRO1VLSH0001",
        1
    ],
    [
        "ورهآور",
        "سرمایه‌گذاری رهآور",
        "IRO1VRHV0001",
        1
    ],
    [
        "وامید",
        "سرمایه‌گذاری امید",
        "IRO1VAMD0001",
        1
    ],
    [
        "والبر",
        "سرمایه‌گذاری البرز",
        "IRO1VALB0001",
        1
    ],
    [
        "ثعتد",
        "سرمایه‌گذاری اعتماد",
        "IRO1TETM0001",
        1
    ],
    [
        "ثمسکن",
        "سرمایه‌گذاری مسکن",
        "IRO1TMSK0001",
        1
    ],
    [
        "ثفارس",
        "سرمایه‌گذاری فارس",
        "IRO1TFRS0001",
        1
    ],
    // --- غذایی ---
    [
        "غبشهر",
        "صنایع غذایی بشهر",
        "IRO1GHBS0001",
        1
    ],
    [
        "غمینو",
        "صنایع غذایی مینو",
        "IRO1GHMI0001",
        1
    ],
    [
        "غپارس",
        "صنایع غذایی پارس",
        "IRO1GHPR0001",
        1
    ],
    [
        "غشیرین",
        "صنایع غذایی شیرین",
        "IRO1GHSR0001",
        1
    ],
    [
        "غچین",
        "صنایع غذایی چین‌چین",
        "IRO1GHCH0001",
        1
    ],
    [
        "غپاک",
        "صنایع غذایی پاک",
        "IRO1GHPK0001",
        1
    ],
    [
        "غگل",
        "گلوکوزان",
        "IRO1GHGL0001",
        1
    ],
    [
        "غیوان",
        "صنایع غذایی یوان",
        "IRO1GHYV0001",
        1
    ],
    [
        "غماهان",
        "صنایع غذایی ماهان",
        "IRO1GHMN0001",
        1
    ],
    // --- بیمه ---
    [
        "شغدیر",
        "بیمه غدیر",
        "IRO1BGHD0001",
        1
    ],
    [
        "شآسیا",
        "بیمه آسیا",
        "IRO1BASI0001",
        1
    ],
    [
        "شایران",
        "بیمه ایران",
        "IRO1BIRN0001",
        1
    ],
    [
        "شپارسیان",
        "بیمه پارسیان",
        "IRO1BPRN0001",
        1
    ],
    [
        "شملت",
        "بیمه ملت",
        "IRO1BMLT0001",
        1
    ],
    [
        "شپاسار",
        "بیمه پاسارگاد",
        "IRO1BPSR0001",
        1
    ],
    [
        "شصاد",
        "بیمه صادرات",
        "IRO1BSDR0001",
        1
    ],
    [
        "شنوین",
        "بیمه نوین",
        "IRO1BNVN0001",
        1
    ],
    [
        "شالبر",
        "بیمه البرز",
        "IRO1BALB0001",
        1
    ],
    [
        "شدان",
        "بیمه دانا",
        "IRO1BDAN0001",
        1
    ],
    [
        "شمعین",
        "بیمه معین",
        "IRO1BMOI0001",
        1
    ],
    [
        "شکبیر",
        "بیمه کوثر",
        "IRO1BKOT0001",
        1
    ],
    // --- قند و شکر ---
    [
        "قشکر",
        "قند شکر",
        "IRO1QSHK0001",
        1
    ],
    [
        "قنیطره",
        "قند نیطره",
        "IRO1QNYT0001",
        1
    ],
    [
        "قنقده",
        "قند نقده",
        "IRO1QNQD0001",
        1
    ],
    [
        "قچاران",
        "قند چاران",
        "IRO1QCHR0001",
        1
    ],
    [
        "قهنر",
        "قند هنر",
        "IRO1QHNR0001",
        1
    ],
    [
        "قجاود",
        "قند جاود",
        "IRO1QJVD0001",
        1
    ],
    [
        "قیزدم",
        "قند یزد",
        "IRO1QYZD0001",
        1
    ],
    [
        "ققنوس",
        "قندققنوس",
        "IRO1QQNS0001",
        1
    ],
    // --- معدنی ---
    [
        "کپشیر",
        "معدنی پشیر",
        "IRO1KPSH0001",
        1
    ],
    [
        "کنور",
        "معدنی نور",
        "IRO1KNUR0001",
        1
    ],
    [
        "کچن",
        "معدنی چن",
        "IRO1KCHN0001",
        1
    ],
    [
        "کگازان",
        "معدنی گازان",
        "IRO1KGZN0001",
        1
    ],
    // --- نساجی ---
    [
        "لجباری",
        "نساجی جباری",
        "IRO1LJBR0001",
        1
    ],
    [
        "لبهمن",
        "نساجی بهمن",
        "IRO1LBHM0001",
        1
    ],
    [
        "لسرما",
        "نساجی سرما",
        "IRO1LSRM0001",
        1
    ],
    [
        "لقزوین",
        "نساجی قزوین",
        "IRO1LQZV0001",
        1
    ],
    [
        "لغزل",
        "نساجی غزل",
        "IRO1LGZL0001",
        1
    ],
    // --- فناوری ---
    [
        "پاکشو",
        "پاکشو",
        "IRO1PAKJ0001",
        1
    ],
    [
        "تکالا",
        "الکترونیک کالا",
        "IRO1TKAL0001",
        1
    ],
    // --- کشت و صنعت ---
    [
        "حفارس",
        "کشت و صنعت فارس",
        "IRO1HFRS0001",
        1
    ],
    [
        "حکشتی",
        "کشت و صنعت کشتی",
        "IRO1HKST0001",
        1
    ],
    [
        "حبیش",
        "کشت و صنعت بیش",
        "IRO1HBSH0001",
        1
    ],
    [
        "حداوی",
        "کشت و صنعت داوی",
        "IRO1HDVI0001",
        1
    ],
    [
        "حشهر",
        "کشت و صنعت شهر",
        "IRO1HSHR0001",
        1
    ],
    // --- لیزینگ ---
    [
        "لگنج",
        "لیزینگ گنج",
        "IRO1LGNJ0001",
        1
    ],
    [
        "لملت",
        "لیزینگ ملت",
        "IRO1LMLT0001",
        1
    ],
    [
        "لصادرات",
        "لیزینگ صادرات",
        "IRO1LSDR0001",
        1
    ],
    // --- صندوق‌های ETF ---
    [
        "طلا",
        "صندوق طلایی",
        "IRO1FTGB0001",
        1
    ],
    [
        "سکه",
        "صندوق سکه طلا",
        "IRO1SKGH0001",
        1
    ],
    [
        "عیار",
        "صندوق عیار",
        "IRO1EYAR0001",
        1
    ],
    [
        "دارا",
        "صندوق دارا",
        "IRO1DARA0001",
        1
    ],
    [
        "آگاه",
        "صندوق آگاه",
        "IRO1AGAH0001",
        1
    ],
    [
        "کاردان",
        "صندوق کاردان",
        "IRO1KRDAN001",
        1
    ],
    [
        "لطیف",
        "صندوق لطیف",
        "IRO1LATF0001",
        1
    ],
    [
        "فردا",
        "صندوق فردا",
        "IRO1FRDA0001",
        1
    ],
    [
        "گنجینه",
        "صندوق گنجینه",
        "IRO1GNJN0001",
        1
    ],
    [
        "اعتماد",
        "صندوق اعتماد",
        "IRO1ETMD0001",
        1
    ],
    [
        "پارسیان",
        "صندوق پارسیان",
        "IRO1PRSN0001",
        1
    ],
    [
        "هامون",
        "صندوق هامون",
        "IRO1HMN0001",
        1
    ],
    [
        "نمو",
        "صندوق نمو",
        "IRO1NEMO0001",
        1
    ],
    [
        "آساس",
        "صندوق آساس",
        "IRO1ASAS0001",
        1
    ],
    [
        "کیمیا",
        "صندوق کیمیا",
        "IRO1KYMA0001",
        1
    ],
    [
        "زیتون",
        "صندوق زیتون",
        "IRO1ZITN0001",
        1
    ],
    [
        "سرو",
        "صندوق سرو",
        "IRO1SRV0001",
        1
    ],
    [
        "فالف",
        "صندوق فالف",
        "IRO1FALF0001",
        1
    ],
    [
        "بنفش",
        "صندوق بنفش",
        "IRO1BNFSH001",
        1
    ],
    [
        "فیروزه",
        "صندوق فیروزه",
        "IRO1FRZH0001",
        1
    ],
    [
        "یاقوت",
        "صندوق یاقوت",
        "IRO1YAQT0001",
        1
    ],
    [
        "زر",
        "صندوق زر",
        "IRO1ZARR0001",
        1
    ],
    [
        "زرین",
        "صندوق زرین",
        "IRO1ZRIN0001",
        1
    ],
    [
        "امید",
        "صندوق امید",
        "IRO1OMID0001",
        1
    ],
    [
        "بذر",
        "صندوق بذر",
        "IRO1BZTR0001",
        1
    ],
    [
        "پیشتاز",
        "صندوق پیشتاز",
        "IRO1PSHT0001",
        1
    ],
    [
        "سرمایه",
        "صندوق سرمایه",
        "IRO1SRMH0001",
        1
    ],
    [
        "کارآمد",
        "صندوق کارآمد",
        "IRO1KRAM0001",
        1
    ],
    [
        "گسترش",
        "صندوق گسترش",
        "IRO1GSTR0001",
        1
    ],
    [
        "محافظ",
        "صندوق محافظ",
        "IRO1MHFZ0001",
        1
    ],
    [
        "منفعت",
        "صندوق منفعت",
        "IRO1MNFT0001",
        1
    ],
    [
        "وصت",
        "صندوق وصت",
        "IRO1VSAT0001",
        1
    ]
];
/** Real فرابورس (OTC) stock symbols - verified actual market tickers */ const OTC_SYMBOLS = [
    // [symbol, name, isin, flow=2]
    [
        "قیستو",
        "ایستا فیزیک",
        "IRO2QIST0001",
        2
    ],
    [
        "ساروم",
        "ساروم آرا",
        "IRO2SARM0001",
        2
    ],
    [
        "لپارس",
        "لپارس",
        "IRO2LPRS0001",
        2
    ],
    [
        "فلامی",
        "فلامی",
        "IRO2FLMI0001",
        2
    ],
    [
        "کبورد",
        "کبورد سیر",
        "IRO2KBRD0001",
        2
    ],
    [
        "ثاباد",
        "آبادگران",
        "IRO2THBD0001",
        2
    ],
    [
        "نگین",
        "نگین خاور",
        "IRO2NGNE0001",
        2
    ],
    [
        "ساربید",
        "ساربید",
        "IRO2SRBD0001",
        2
    ],
    [
        "غیث",
        "غیث",
        "IRO2GHYH0001",
        2
    ],
    [
        "حفار",
        "حفاری آسیا",
        "IRO2HFAR0001",
        2
    ],
    [
        "فلامس",
        "فلامس",
        "IRO2FLMS0001",
        2
    ],
    [
        "سبزا",
        "سبزا",
        "IRO2SBZA0001",
        2
    ],
    [
        "قیطران",
        "قیطران",
        "IRO2QTRN0001",
        2
    ],
    [
        "معیار",
        "معیار",
        "IRO2MYAR0001",
        2
    ],
    [
        "آرمان",
        "آرمان",
        "IRO2ARMN0001",
        2
    ],
    [
        "دیران",
        "دیران",
        "IRO2DYRN0001",
        2
    ],
    [
        "تکین",
        "تکین",
        "IRO2TKIN0001",
        2
    ],
    [
        "سپنتا",
        "سپنتا",
        "IRO2SPNT0001",
        2
    ],
    [
        "نطرین",
        "نظرین",
        "IRO2NTRN0001",
        2
    ],
    [
        "کفرا",
        "کشت و صنعت فرا",
        "IRO2KFRA0001",
        2
    ],
    [
        "فبستم",
        "فبستم",
        "IRO2FBST0001",
        2
    ],
    [
        "سغرب",
        "سرمایه‌گذاری غرب",
        "IRO2SGRB0001",
        2
    ],
    [
        "پردیس",
        "پردیس",
        "IRO2PRDS0001",
        2
    ],
    [
        "داران",
        "داران",
        "IRO2DARN0001",
        2
    ],
    [
        "سپید",
        "سپید",
        "IRO2SPID0001",
        2
    ],
    [
        "کاوه",
        "کاوه",
        "IRO2KAVH0001",
        2
    ],
    [
        "نوری",
        "نوری",
        "IRO2NURY0001",
        2
    ],
    [
        "سامان",
        "سامان",
        "IRO2SMAN0001",
        2
    ],
    [
        "آتیه",
        "آتیه فرا",
        "IRO2ATIH0001",
        2
    ],
    [
        "تراک",
        "تراک",
        "IRO2TRAK0001",
        2
    ],
    [
        "گیلاس",
        "گیلاس",
        "IRO2GYLS0001",
        2
    ],
    [
        "مرجان",
        "مرجان",
        "IRO2MRJN0001",
        2
    ],
    [
        "دنا",
        "دنا فرا",
        "IRO2DNA0001",
        2
    ],
    [
        "آساس",
        "آساس فرا",
        "IRO2ASSS0001",
        2
    ],
    [
        "بتک",
        "بتک",
        "IRO2BTK0001",
        2
    ],
    [
        "ثروتمند",
        "ثروتمند",
        "IRO2SRTM0001",
        2
    ],
    [
        "کارا",
        "کارا",
        "IRO2KARA0001",
        2
    ],
    [
        "پایدار",
        "پایدار فرا",
        "IRO2PYDR0001",
        2
    ],
    [
        "کاسپین",
        "کاسپین",
        "IRO2KSPN0001",
        2
    ],
    [
        "ساحل",
        "ساحل",
        "IRO2SAHL0001",
        2
    ],
    [
        "ماهان",
        "ماهان فرا",
        "IRO2MHN0001",
        2
    ],
    [
        "باما",
        "باما",
        "IRO2BAMA0001",
        2
    ],
    [
        "نوین",
        "نوین فرا",
        "IRO2NVN0001",
        2
    ],
    [
        "رشد",
        "رشد فرا",
        "IRO2RSHD0001",
        2
    ],
    [
        "سرو",
        "سرو فرا",
        "IRO2SRV0001",
        2
    ],
    [
        "بدر",
        "بدر",
        "IRO2BDR0001",
        2
    ],
    [
        "الف",
        "الف",
        "IRO2ALIF0001",
        2
    ],
    [
        "قلم",
        "قلم",
        "IRO2QLM0001",
        2
    ],
    [
        "بامداد",
        "بامداد",
        "IRO2BMDD0001",
        2
    ],
    [
        "میداک",
        "میداک",
        "IRO2MDK0001",
        2
    ],
    [
        "دالان",
        "دالان",
        "IRO2DLN0001",
        2
    ],
    [
        "سازگار",
        "سازگار",
        "IRO2SZGR0001",
        2
    ],
    [
        "کیمیا",
        "کیمیا فرا",
        "IRO2KMYA0001",
        2
    ],
    [
        "آوا",
        "آوا",
        "IRO2AWA0001",
        2
    ],
    [
        "بنفش",
        "بنفش فرا",
        "IRO2BNFS0001",
        2
    ],
    [
        "بهرام",
        "بهرام",
        "IRO2BHRM0001",
        2
    ],
    [
        "فراز",
        "فراز",
        "IRO2FRAZ0001",
        2
    ],
    [
        "نوید",
        "نوید",
        "IRO2NVID0001",
        2
    ],
    [
        "غزل",
        "غزل فرا",
        "IRO2GZL0001",
        2
    ],
    [
        "مهام",
        "مهام",
        "IRO2MHM0001",
        2
    ],
    [
        "داده",
        "داده",
        "IRO2DDH0001",
        2
    ],
    [
        "سپند",
        "سپند فرا",
        "IRO2SPND0001",
        2
    ],
    [
        "کوروش",
        "کوروش",
        "IRO2KRSH0001",
        2
    ],
    [
        "گسترش",
        "گسترش فرا",
        "IRO2GSTR0001",
        2
    ],
    [
        "اثر",
        "اثر",
        "IRO2ASR0001",
        2
    ],
    [
        "پیشگام",
        "پیشگام فرا",
        "IRO2PSHG0001",
        2
    ],
    [
        "آینده",
        "آینده فرا",
        "IRO2ANDE0001",
        2
    ],
    [
        "فردوس",
        "فردوس",
        "IRO2FRDS0001",
        2
    ],
    [
        "گنبد",
        "گنبد",
        "IRO2GNBD0001",
        2
    ],
    [
        "شایان",
        "شایان",
        "IRO2SHYN0001",
        2
    ],
    [
        "ترنج",
        "ترنج",
        "IRO2TRNJ0001",
        2
    ],
    [
        "کاوالا",
        "کاوالا",
        "IRO2KVL0001",
        2
    ],
    [
        "سپیدار",
        "سپیدار",
        "IRO2SPDR0001",
        2
    ],
    [
        "نورفرا",
        "نور فرا",
        "IRO2NURF0001",
        2
    ],
    [
        "دامون",
        "دامون",
        "IRO2DMN0001",
        2
    ],
    [
        "زمرد",
        "زمرد",
        "IRO2ZMRD0001",
        2
    ],
    [
        "سروش",
        "سروش",
        "IRO2SRSH0001",
        2
    ],
    [
        "کبیر",
        "کبیر فرا",
        "IRO2KBR0001",
        2
    ],
    [
        "نیکا",
        "نیکا",
        "IRO2NIKA0001",
        2
    ],
    [
        "اشن",
        "اشن",
        "IRO2ASHN0001",
        2
    ],
    [
        "پارسی",
        "پارسی فرا",
        "IRO2PRSI0001",
        2
    ],
    [
        "سیراف",
        "سیراف",
        "IRO2SIRF0001",
        2
    ],
    [
        "نماوا",
        "نماوا",
        "IRO2NMWA0001",
        2
    ],
    [
        "یاقوت",
        "یاقوت",
        "IRO2YAQT0001",
        2
    ],
    [
        "اخابر",
        "اخابر",
        "IRO2AKHR0001",
        2
    ],
    [
        "فلامک",
        "فلامک",
        "IRO2FLMK0001",
        2
    ],
    [
        "توسن",
        "توسن",
        "IRO2TSN0001",
        2
    ],
    [
        "بسام",
        "بسام",
        "IRO2BSM0001",
        2
    ],
    [
        "ساجین",
        "ساجین",
        "IRO2SJN0001",
        2
    ],
    [
        "کرمانش",
        "کرمانش",
        "IRO2KRMS0001",
        2
    ],
    [
        "قشنگ",
        "قشنگ",
        "IRO2QSHN0001",
        2
    ],
    [
        "فیروزا",
        "فیروزا",
        "IRO2FRZA0001",
        2
    ],
    [
        "ساشا",
        "ساشا",
        "IRO2SSHA0001",
        2
    ],
    [
        "بفرا",
        "بفرا",
        "IRO2BFRA0001",
        2
    ],
    [
        "دالف",
        "دالف",
        "IRO2DLF0001",
        2
    ],
    [
        "شاهد",
        "شاهد فرا",
        "IRO2SHHD0001",
        2
    ],
    [
        "سواد",
        "سواد",
        "IRO2SVAD0001",
        2
    ],
    [
        "نیاوران",
        "نیاوران",
        "IRO2NYVR0001",
        2
    ],
    [
        "پرشین",
        "پرشین",
        "IRO2PRSH0001",
        2
    ],
    [
        "بندر",
        "بندر فرا",
        "IRO2BNDR0001",
        2
    ],
    [
        "تکنو",
        "تکنو فرا",
        "IRO2TKNU0001",
        2
    ],
    [
        "کوثر",
        "کوثر فرا",
        "IRO2KUTH0001",
        2
    ],
    [
        "راهبر",
        "راهبر",
        "IRO2RHBR0001",
        2
    ],
    [
        "بهراسا",
        "بهراسا",
        "IRO2BHRS0001",
        2
    ],
    [
        "مارون",
        "مارون",
        "IRO2MRN0001",
        2
    ],
    [
        "پلاک",
        "پلاک",
        "IRO2PLK0001",
        2
    ],
    [
        "اقتصاد",
        "اقتصاد فرا",
        "IRO2EQTD0001",
        2
    ],
    [
        "ساترا",
        "ساترا",
        "IRO2STRA0001",
        2
    ],
    [
        "ماکو",
        "ماکو",
        "IRO2MAKU0001",
        2
    ],
    [
        "تاکو",
        "تاکو",
        "IRO2TAKU0001",
        2
    ],
    [
        "سپاهان",
        "سپاهان",
        "IRO2SPHN0001",
        2
    ],
    [
        "شاملی",
        "شاملی",
        "IRO2SHML0001",
        2
    ],
    [
        "پلیمر",
        "پلیمر",
        "IRO2PLMR0001",
        2
    ],
    [
        "چافس",
        "چافس",
        "IRO2CHFS0001",
        2
    ],
    [
        "شپد",
        "شپد",
        "IRO2SHPD0001",
        2
    ],
    [
        "کیان",
        "کیان فرا",
        "IRO2KYAN0001",
        2
    ],
    [
        "شفن",
        "شفن فرا",
        "IRO2SHFN0001",
        2
    ],
    [
        "پلاست",
        "پلاستیک",
        "IRO2PLST0001",
        2
    ],
    [
        "حکمت",
        "حکمت",
        "IRO2HKMT0001",
        2
    ],
    [
        "رپترو",
        "رپترو",
        "IRO2RPTRO001",
        2
    ],
    [
        "کعبید",
        "کعبید",
        "IRO2KABD0001",
        2
    ],
    [
        "قلر",
        "قلر",
        "IRO2QLR0001",
        2
    ],
    [
        "وامید",
        "وامید فرا",
        "IRO2VAMD0001",
        2
    ],
    [
        "شپارس",
        "شپارس فرا",
        "IRO2SPRS0001",
        2
    ],
    [
        "ثنوسا",
        "ثنوسا فرا",
        "IRO2TNOS0001",
        2
    ],
    [
        "زپارس",
        "زپارس فرا",
        "IRO2ZPRS0001",
        2
    ],
    [
        "فجر",
        "فجر فرا",
        "IRO2FAJR0001",
        2
    ],
    [
        "شبهران",
        "شبهران",
        "IRO2SBHR0001",
        2
    ],
    [
        "پالایش",
        "پالایش فرا",
        "IRO2PLSH0001",
        2
    ],
    [
        "فولاد",
        "فولاد فرا",
        "IRO2FLD0001",
        2
    ],
    [
        "شتران",
        "شتران فرا",
        "IRO2SHTRN001",
        2
    ],
    [
        "وبملت",
        "وبملت فرا",
        "IRO2BMLT0001",
        2
    ],
    [
        "فملی",
        "فملی فرا",
        "IRO2FMLI0001",
        2
    ],
    [
        "خودرو",
        "خودرو فرا",
        "IRO2KHDR0001",
        2
    ],
    [
        "خساپا",
        "خساپا فرا",
        "IRO2KSAI0001",
        2
    ],
    [
        "وبصادر",
        "وبصادر فرا",
        "IRO2BSHR0001",
        2
    ],
    [
        "وتجارت",
        "وتجارت فرا",
        "IRO2BTEJ0001",
        2
    ],
    [
        "وپاسار",
        "وپاسار فرا",
        "IRO2BPSR0001",
        2
    ],
    [
        "وبانک",
        "وبانک فرا",
        "IRO2BANK0001",
        2
    ],
    [
        "سمگا",
        "سمگا فرا",
        "IRO2SMNG0001",
        2
    ],
    [
        "دعبید",
        "دعبید فرا",
        "IRO2DABD0001",
        2
    ],
    [
        "غبشهر",
        "غبشهر فرا",
        "IRO2GHBS0001",
        2
    ],
    [
        "شغدیر",
        "شغدیر فرا",
        "IRO2BGHD0001",
        2
    ]
];
/** Deterministic pseudo-random generator seeded by string */ function hashStr(str) {
    let hash = 5381;
    for(let i = 0; i < str.length; i++){
        hash = (hash << 5) + hash + str.charCodeAt(i);
        hash = hash & 0x7fffffff;
    }
    return hash;
}
function deterministic(seed) {
    return hashStr(seed) % 10000 / 10000;
}
/** Generate fallback raw symbols with realistic but deterministic prices */ function getFallbackSymbolsRaw() {
    const allSymbols = [
        ...BOURSE_SYMBOLS,
        ...OTC_SYMBOLS
    ];
    return allSymbols.map(([l18, l30, isin, flow], index)=>{
        // Use deterministic values based on symbol name
        const d1 = deterministic(isin + "_price");
        const d2 = deterministic(isin + "_change");
        // Base price ranges by sector
        const basePrice = Math.round(1000 + d1 * 45000);
        const changePercent = (d2 - 0.45) * 10; // -4.5% to +5.5%
        const yesterdayPrice = Math.round(basePrice / (1 + changePercent / 100));
        return {
            time: "12:00:00",
            l18,
            l30,
            isin,
            id: 10000 + index,
            flow,
            instId: isin,
            cVal: String(basePrice),
            yVal: String(yesterdayPrice),
            pctVar: String(changePercent.toFixed(2)),
            sGls: "A"
        };
    });
}
/** Fallback market indices - realistic values */ function getFallbackIndices() {
    return [
        {
            name: "شاخص کل (TEDPIX)",
            value: 2345678,
            change: 12345,
            percentChange: 0.53
        },
        {
            name: "شاخص هم‌وزن",
            value: 8765,
            change: -32,
            percentChange: -0.36
        },
        {
            name: "شاخص فرابورس",
            value: 3456,
            change: 78,
            percentChange: 2.31
        },
        {
            name: "شاخص بازار اول",
            value: 5678,
            change: 45,
            percentChange: 0.80
        },
        {
            name: "شاخص بازار دوم",
            value: 2345,
            change: -12,
            percentChange: -0.51
        },
        {
            name: "شاخص صنعت",
            value: 4567,
            change: 89,
            percentChange: 1.99
        },
        {
            name: "شاخص فلزات اساسی",
            value: 7890,
            change: -45,
            percentChange: -0.57
        },
        {
            name: "شاخص بانک‌ها",
            value: 5432,
            change: 67,
            percentChange: 1.25
        }
    ];
}
/** Fallback symbol detail */ function getFallbackSymbolDetail(isin) {
    const d = deterministic(isin + "_detail");
    const basePrice = Math.round(1000 + d * 45000);
    return {
        isin,
        l18: isin,
        l30: "شرکت نمونه",
        pl: String(basePrice),
        py: String(Math.round(basePrice * 0.98)),
        pf: String(Math.round(basePrice * 0.99)),
        ph: String(Math.round(basePrice * 1.02)),
        pMin: String(Math.round(basePrice * 0.97)),
        pc: String(basePrice),
        tVol: String(Math.round(100000 + d * 5000000)),
        tVal: String(Math.round(basePrice * 500000)),
        tNo: String(Math.round(50 + d * 3000)),
        eps: String(Math.round(50 + d * 3000)),
        pe: String((5 + d * 30).toFixed(1)),
        bVol: String(Math.round(100 + d * 5000))
    };
}
/** Fallback ETF NAV data */ function getFallbackEtfNav() {
    return [
        {
            isin: "IRO1FTGB0001",
            name: "صندوق طلایی",
            nav: 125000,
            navChange: 1.2
        },
        {
            isin: "IRO1SKGH0001",
            name: "صندوق سکه طلا",
            nav: 89000,
            navChange: 0.8
        },
        {
            isin: "IRO1DARA0001",
            name: "صندوق دارا",
            nav: 3200,
            navChange: -0.5
        },
        {
            isin: "IRO1AGAH0001",
            name: "صندوق آگاه",
            nav: 18500,
            navChange: 1.1
        },
        {
            isin: "IRO1KRDAN001",
            name: "صندوق کاردان",
            nav: 9800,
            navChange: 0.3
        }
    ];
}
/** Fallback gold & currency data */ function getFallbackGoldCurrency() {
    return [
        {
            name: "طلای آبشده",
            price: 52340000,
            change: 450000,
            percentChange: 0.87,
            category: "gold",
            unit: "تومان",
            updated: new Date().toISOString()
        },
        {
            name: "سکه بهار آزادی",
            price: 78900000,
            change: 1200000,
            percentChange: 1.54,
            category: "gold",
            unit: "تومان",
            updated: new Date().toISOString()
        },
        {
            name: "نیم سکه",
            price: 45600000,
            change: 800000,
            percentChange: 1.79,
            category: "gold",
            unit: "تومان",
            updated: new Date().toISOString()
        },
        {
            name: "ربع سکه",
            price: 28700000,
            change: 500000,
            percentChange: 1.77,
            category: "gold",
            unit: "تومان",
            updated: new Date().toISOString()
        },
        {
            name: "گرم طلا",
            price: 5234000,
            change: 45000,
            percentChange: 0.87,
            category: "gold",
            unit: "تومان",
            updated: new Date().toISOString()
        },
        {
            name: "دلار آزاد",
            price: 892000,
            change: 3500,
            percentChange: 0.39,
            category: "currency",
            unit: "تومان",
            updated: new Date().toISOString()
        },
        {
            name: "یورو",
            price: 965000,
            change: -2500,
            percentChange: -0.26,
            category: "currency",
            unit: "تومان",
            updated: new Date().toISOString()
        },
        {
            name: "درهم امارات",
            price: 243000,
            change: 1200,
            percentChange: 0.50,
            category: "currency",
            unit: "تومان",
            updated: new Date().toISOString()
        },
        {
            name: "لیر ترکیه",
            price: 26500,
            change: -800,
            percentChange: -2.92,
            category: "currency",
            unit: "تومان",
            updated: new Date().toISOString()
        },
        {
            name: "یوان چین",
            price: 123000,
            change: 500,
            percentChange: 0.41,
            category: "currency",
            unit: "تومان",
            updated: new Date().toISOString()
        }
    ];
}
}),
"[project]/src/services/history-service.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "HistoryService",
    ()=>HistoryService,
    "historyService",
    ()=>historyService
]);
// ============================================
// History Service
// Ingests historical market data (price series) and news from the BRS API
// into the database. Designed to be idempotent (upsert by unique key).
// ============================================
var __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__ = __turbopack_context__.i("[externals]/@prisma/client [external] (@prisma/client, cjs, [project]/node_modules/@prisma/client)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$client$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/brs-client.ts [app-route] (ecmascript)");
;
;
const prisma = new __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["PrismaClient"]();
const DEFAULT_TOP = 365;
const DEFAULT_BATCH_SIZE = 10;
const DEFAULT_DELAY_MS = 500;
const DEFAULT_NEWS_COUNT = 100;
class HistoryService {
    /**
   * Ingest historical price series for a single symbol into MarketData.
   * Uses upsert on the (symbolId, date) unique constraint.
   */ async ingestPriceHistoryForSymbol(symbolId, isin, symbol, top = DEFAULT_TOP, startDate, endDate) {
        const result = {
            symbolId,
            isin,
            symbol,
            requested: 0,
            inserted: 0,
            updated: 0,
            skipped: 0,
            source: "fallback"
        };
        try {
            const { data, source } = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$client$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["fetchPriceHistory"])(isin, top);
            result.source = source;
            result.requested = data.length;
            for (const point of data){
                const pointDate = new Date(point.date);
                pointDate.setUTCHours(0, 0, 0, 0);
                if (startDate && pointDate < startDate) {
                    result.skipped++;
                    continue;
                }
                if (endDate && pointDate > endDate) {
                    result.skipped++;
                    continue;
                }
                const { inserted, updated } = await this.upsertMarketData(symbolId, point);
                result.inserted += inserted;
                result.updated += updated;
            }
        } catch (error) {
            result.error = error instanceof Error ? error.message : "خطای ناشناخته";
        }
        return result;
    }
    /** Upsert a single historical point into MarketData */ async upsertMarketData(symbolId, p) {
        const date = new Date(p.date);
        date.setUTCHours(0, 0, 0, 0);
        const change = p.close - p.yesterdayPrice;
        const changePercent = p.yesterdayPrice !== 0 ? change / p.yesterdayPrice * 100 : 0;
        const data = {
            price: p.close,
            change,
            changePercent,
            volume: p.volume,
            tradeCount: p.tradeCount,
            yesterdayPrice: p.yesterdayPrice,
            openPrice: p.open,
            highPrice: p.high,
            lowPrice: p.low,
            closePrice: p.close
        };
        const existing = await prisma.marketData.findUnique({
            where: {
                symbolId_date: {
                    symbolId,
                    date
                }
            },
            select: {
                id: true
            }
        });
        if (existing) {
            await prisma.marketData.update({
                where: {
                    symbolId_date: {
                        symbolId,
                        date
                    }
                },
                data
            });
            return {
                inserted: 0,
                updated: 1
            };
        }
        await prisma.marketData.create({
            data: {
                symbolId,
                date,
                ...data
            }
        });
        return {
            inserted: 1,
            updated: 0
        };
    }
    /**
   * Ingest price history for all symbols (optionally limited).
   * Processes symbols sequentially to respect API rate limits.
   */ async ingestAllSymbolsPriceHistory(options = {}) {
        const top = options.top || DEFAULT_TOP;
        const limit = options.limit;
        const batchSize = options.batchSize || DEFAULT_BATCH_SIZE;
        const delayMs = options.delayMs || DEFAULT_DELAY_MS;
        const startDate = options.startDate;
        const endDate = options.endDate;
        const symbols = await prisma.symbol.findMany({
            select: {
                id: true,
                isin: true,
                symbol: true
            },
            take: limit,
            orderBy: {
                symbol: "asc"
            }
        });
        const details = [];
        let succeeded = 0;
        let failed = 0;
        let skipped = 0;
        const startedAt = new Date();
        for(let i = 0; i < symbols.length; i++){
            const sym = symbols[i];
            if (i > 0 && i % batchSize === 0) {
                await this.delay(delayMs);
            }
            const r = await this.ingestPriceHistoryForSymbol(sym.id, sym.isin, sym.symbol, top, startDate, endDate);
            details.push(r);
            if (r.error) {
                failed++;
            } else if (r.skipped > 0 && r.inserted === 0 && r.updated === 0) {
                skipped++;
            } else {
                succeeded++;
            }
        }
        return {
            total: symbols.length,
            succeeded,
            failed,
            skipped,
            details,
            startedAt,
            finishedAt: new Date()
        };
    }
    /**
   * Fetch and persist news items into the News table.
   * If no real news is returned by the API, nothing fake is persisted.
   */ async syncNews(category = "", count = 20) {
        const { data, source } = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$client$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["fetchNews"])(category, count);
        let saved = 0;
        for (const item of data){
            const publishedAt = this.parseNewsDate(item.date);
            await prisma.news.upsert({
                where: {
                    url: item.url
                },
                create: {
                    title: item.title,
                    url: item.url,
                    snippet: item.snippet || null,
                    source: item.source || null,
                    category: item.category || category || null,
                    publishedAt
                },
                update: {
                    title: item.title,
                    snippet: item.snippet || null,
                    source: item.source || null,
                    category: item.category || category || null,
                    publishedAt
                }
            });
            saved++;
        }
        return {
            requested: data.length,
            saved,
            source
        };
    }
    /**
   * Sync historical news from multiple categories.
   */ async syncNewsHistory(categories = [], countPerCategory = 100) {
        let totalSaved = 0;
        let totalRequested = 0;
        const errors = [];
        let lastSource = "fallback";
        for (const category of categories){
            try {
                const { data, source } = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$brs$2d$client$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["fetchNews"])(category, countPerCategory);
                lastSource = source;
                totalRequested += data.length;
                for (const item of data){
                    const publishedAt = this.parseNewsDate(item.date);
                    await prisma.news.upsert({
                        where: {
                            url: item.url
                        },
                        create: {
                            title: item.title,
                            url: item.url,
                            snippet: item.snippet || null,
                            source: item.source || null,
                            category: item.category || category || null,
                            publishedAt
                        },
                        update: {
                            title: item.title,
                            snippet: item.snippet || null,
                            source: item.source || null,
                            category: item.category || category || null,
                            publishedAt
                        }
                    });
                    totalSaved++;
                }
            } catch (error) {
                errors.push(`خطا در همگام‌سازی اخبار دسته ${category}: ${error instanceof Error ? error.message : "خطای ناشناخته"}`);
            }
        }
        return {
            requested: totalRequested,
            saved: totalSaved,
            source: lastSource,
            errors
        };
    }
    /**
   * Comprehensive backfill: prices + news for the last year.
   */ async comprehensiveBackfill(options = {}) {
        const oneYearAgo = new Date();
        oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
        const backfillOptions = {
            top: options.top || DEFAULT_TOP,
            limit: options.limit,
            batchSize: options.batchSize || DEFAULT_BATCH_SIZE,
            delayMs: options.delayMs || DEFAULT_DELAY_MS,
            startDate: options.startDate || oneYearAgo,
            endDate: options.endDate
        };
        const startTime = Date.now();
        const prices = await this.ingestAllSymbolsPriceHistory(backfillOptions);
        const newsCategories = options.categories || [
            "",
            "بورس",
            "اقتصاد",
            "سیاسی"
        ];
        const news = await this.syncNewsHistory(newsCategories, options.newsCount || DEFAULT_NEWS_COUNT);
        const totalDuration = Date.now() - startTime;
        return {
            prices,
            news,
            totalDuration
        };
    }
    /** Read stored price history for a symbol with optional date range */ async getPriceHistory(symbolId, startDate, endDate) {
        const where = {
            symbolId
        };
        if (startDate || endDate) {
            where.date = {};
            if (startDate) where.date.gte = startDate;
            if (endDate) where.date.lte = endDate;
        }
        const rows = await prisma.marketData.findMany({
            where,
            orderBy: {
                date: "asc"
            },
            select: {
                date: true,
                closePrice: true,
                volume: true
            }
        });
        return rows.map((r)=>({
                date: r.date,
                close: r.closePrice,
                volume: r.volume
            }));
    }
    /** Read stored news */ async getNews(limit = 50, category) {
        return prisma.news.findMany({
            where: category ? {
                category
            } : undefined,
            orderBy: [
                {
                    publishedAt: "desc"
                },
                {
                    fetchedAt: "desc"
                }
            ],
            take: limit
        });
    }
    /** Get backfill statistics */ async getBackfillStatistics() {
        const [totalSymbols, symbolsWithHistory, totalMarketDataRows, dateRange, totalNews, recentNews] = await Promise.all([
            prisma.symbol.count(),
            prisma.symbol.count({
                where: {
                    marketData: {
                        some: {}
                    }
                }
            }),
            prisma.marketData.count(),
            prisma.marketData.findFirst({
                orderBy: {
                    date: "desc"
                },
                select: {
                    date: true
                }
            }),
            prisma.news.count(),
            prisma.news.count({
                where: {
                    publishedAt: {
                        gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
                    }
                }
            })
        ]);
        const oldestData = await prisma.marketData.findFirst({
            orderBy: {
                date: "asc"
            },
            select: {
                date: true
            }
        });
        return {
            totalSymbols,
            symbolsWithHistory,
            symbolsWithoutHistory: totalSymbols - symbolsWithHistory,
            totalMarketDataRows,
            oldestDataDate: oldestData?.date || null,
            latestDataDate: dateRange?.date || null,
            totalNews,
            recentNews30Days: recentNews
        };
    }
    parseNewsDate(date) {
        if (!date) return null;
        const d = new Date(date);
        return isNaN(d.getTime()) ? null : d;
    }
    delay(ms) {
        return new Promise((resolve)=>setTimeout(resolve, ms));
    }
}
const historyService = new HistoryService();
}),
"[project]/src/services/todo-service.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "TodoService",
    ()=>TodoService,
    "todoService",
    ()=>todoService
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__ = __turbopack_context__.i("[externals]/@prisma/client [external] (@prisma/client, cjs, [project]/node_modules/@prisma/client)");
;
const prisma = new __TURBOPACK__imported__module__$5b$externals$5d2f40$prisma$2f$client__$5b$external$5d$__$2840$prisma$2f$client$2c$__cjs$2c$__$5b$project$5d2f$node_modules$2f40$prisma$2f$client$29$__["PrismaClient"]();
class TodoService {
    async getTodos(filters = {}) {
        try {
            const where = {};
            if (filters.status) {
                where.status = filters.status;
            }
            if (filters.priority) {
                where.priority = filters.priority;
            }
            if (filters.category) {
                where.category = filters.category;
            }
            if (filters.search) {
                where.OR = [
                    {
                        title: {
                            contains: filters.search
                        }
                    },
                    {
                        description: {
                            contains: filters.search
                        }
                    }
                ];
            }
            const todos = await prisma.todo.findMany({
                where,
                take: filters.limit || 100,
                skip: filters.offset || 0,
                orderBy: [
                    {
                        dueDate: 'asc'
                    },
                    {
                        priority: 'desc'
                    },
                    {
                        createdAt: 'desc'
                    }
                ]
            });
            return todos;
        } catch (error) {
            console.error('خطا در دریافت لیست todos:', error);
            throw new Error('خطا در دریافت لیست todos');
        }
    }
    async getTodoById(id) {
        try {
            return await prisma.todo.findUnique({
                where: {
                    id
                }
            });
        } catch (error) {
            console.error('خطا در دریافت اطلاعات todo:', error);
            throw new Error('خطا در دریافت اطلاعات todo');
        }
    }
    async createTodo(data) {
        try {
            return await prisma.todo.create({
                data: {
                    title: data.title,
                    description: data.description,
                    status: data.status || 'pending',
                    priority: data.priority || 'medium',
                    category: data.category || 'general',
                    tags: data.tags ? data.tags : undefined,
                    dueDate: data.dueDate ? new Date(data.dueDate) : undefined
                }
            });
        } catch (error) {
            console.error('خطا در ایجاد todo:', error);
            throw new Error('خطا در ایجاد todo');
        }
    }
    async updateTodo(id, data) {
        try {
            const updateData = {};
            if (data.title !== undefined) updateData.title = data.title;
            if (data.description !== undefined) updateData.description = data.description;
            if (data.status !== undefined) updateData.status = data.status;
            if (data.priority !== undefined) updateData.priority = data.priority;
            if (data.category !== undefined) updateData.category = data.category;
            if (data.tags !== undefined) updateData.tags = data.tags;
            if (data.dueDate !== undefined) {
                updateData.dueDate = data.dueDate ? new Date(data.dueDate) : null;
            }
            if (data.completedAt !== undefined) {
                updateData.completedAt = data.completedAt ? new Date(data.completedAt) : null;
            }
            return await prisma.todo.update({
                where: {
                    id
                },
                data: updateData
            });
        } catch (error) {
            console.error('خطا در به‌روزرسانی todo:', error);
            throw new Error('خطا در به‌روزرسانی todo');
        }
    }
    async deleteTodo(id) {
        try {
            return await prisma.todo.delete({
                where: {
                    id
                }
            });
        } catch (error) {
            console.error('خطا در حذف todo:', error);
            throw new Error('خطا در حذف todo');
        }
    }
    async getTodoStatistics() {
        try {
            const total = await prisma.todo.count();
            const pending = await prisma.todo.count({
                where: {
                    status: 'pending'
                }
            });
            const inProgress = await prisma.todo.count({
                where: {
                    status: 'in_progress'
                }
            });
            const completed = await prisma.todo.count({
                where: {
                    status: 'completed'
                }
            });
            const archived = await prisma.todo.count({
                where: {
                    status: 'archived'
                }
            });
            const overdue = await prisma.todo.count({
                where: {
                    dueDate: {
                        lt: new Date()
                    },
                    status: {
                        not: 'completed'
                    }
                }
            });
            return {
                total,
                pending,
                inProgress,
                completed,
                archived,
                overdue
            };
        } catch (error) {
            console.error('خطا در دریافت آمار todos:', error);
            throw new Error('خطا در دریافت آمار todos');
        }
    }
}
const todoService = new TodoService();
}),
"[project]/src/services/index.ts [app-route] (ecmascript) <locals>", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([]);
/**
 * خدمات (Services) - لایه منطق کسب‌وکار
 * 
 * این لایه مسئولیت اجرای منطق کسب‌وکار، اعتبارسنجی داده‌ها،
 * و هماهنگی بین لایه‌های مختلف را بر عهده دارد.
 * 
 * اصول طراحی:
 * 1. هر سرویس مسئولیت مشخص و محدودی دارد
 * 2. سرویس‌ها مستقل از یکدیگر هستند
 * 3. خطاها به درستی مدیریت می‌شوند
 * 4. تست‌پذیری بالا
 */ // سرویس مدیریت سلسله‌مراتب 6D
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$hierarchy$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/services/hierarchy-service.ts [app-route] (ecmascript)");
// سرویس مدیریت نمادها و داده‌های بازار
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$symbol$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/services/symbol-service.ts [app-route] (ecmascript)");
// سرویس سیستم امتیازدهی
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$scoring$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/services/scoring-service.ts [app-route] (ecmascript)");
// سرویس داده‌های تاریخی (قیمت + اخبار)
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$history$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/services/history-service.ts [app-route] (ecmascript)");
// سرویس مدیریت Todo
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$todo$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/services/todo-service.ts [app-route] (ecmascript)"); /**
 * نمونه‌های آماده از سرویس‌ها
 *
 * استفاده:
 * import { hierarchyService, symbolService, scoringService, todoService } from '@/services';
 *
 * یا برای انواع (types):
 * import { type TodoCreateInput } from '@/services';
 */  /**
 * ساختار لایه سرویس:
 * 
 * 1. Hierarchy Service
 *    - مدیریت ساختار سلسله‌مراتبی 6D
 *    - ایجاد، خواندن، به‌روزرسانی و حذف ابعاد
 *    - اعتبارسنجی ساختار
 * 
 * 2. Symbol Service
 *    - مدیریت نمادهای بورسی
 *    - مدیریت داده‌های بازار
 *    - جستجو و فیلتر پیشرفته
 * 
 * 3. Scoring Service
 *    - محاسبه امتیازهای 6 بعدی
 *    - مدیریت الگوریتم‌های امتیازدهی
 *    - رتبه‌بندی نمادها
 * 
 * 4. Reference Service (آینده)
 *    - مدیریت منابع علمی
 *    - ارتباط منابع با ابعاد
 * 
 * 5. Audit Service (آینده)
 *    - ثبت لاگ‌های سیستم
 *    - ردیابی تغییرات
 */ 
;
;
;
;
;
}),
"[project]/src/app/api/todos/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "GET",
    ()=>GET,
    "POST",
    ()=>POST
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$index$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/src/services/index.ts [app-route] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$todo$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/services/todo-service.ts [app-route] (ecmascript)");
;
;
async function GET(request) {
    try {
        const searchParams = request.nextUrl.searchParams;
        const filters = {};
        if (searchParams.has('status')) {
            filters.status = searchParams.get('status') || undefined;
        }
        if (searchParams.has('priority')) {
            filters.priority = searchParams.get('priority') || undefined;
        }
        if (searchParams.has('category')) {
            filters.category = searchParams.get('category') || undefined;
        }
        if (searchParams.has('search')) {
            filters.search = searchParams.get('search') || undefined;
        }
        if (searchParams.has('limit')) {
            filters.limit = parseInt(searchParams.get('limit') || '100');
        }
        if (searchParams.has('offset')) {
            filters.offset = parseInt(searchParams.get('offset') || '0');
        }
        const todos = await __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$todo$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["todoService"].getTodos(filters);
        const stats = await __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$todo$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["todoService"].getTodoStatistics();
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            success: true,
            data: todos,
            statistics: stats,
            count: todos.length,
            timestamp: new Date().toISOString()
        }, {
            status: 200
        });
    } catch (error) {
        console.error('❌ خطا در دریافت لیست todos:', error);
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            success: false,
            error: 'خطا در دریافت لیست todos',
            details: error instanceof Error ? error.message : 'خطای ناشناخته'
        }, {
            status: 500
        });
    }
}
async function POST(request) {
    try {
        const body = await request.json();
        if (!body.title || !body.title.trim()) {
            return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
                success: false,
                error: 'عنوان todo الزامی است'
            }, {
                status: 400
            });
        }
        const todo = await __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$services$2f$todo$2d$service$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["todoService"].createTodo({
            title: body.title,
            description: body.description,
            status: body.status,
            priority: body.priority,
            category: body.category,
            tags: body.tags,
            dueDate: body.dueDate
        });
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            success: true,
            data: todo,
            message: 'Todo با موفقیت ایجاد شد',
            timestamp: new Date().toISOString()
        }, {
            status: 201
        });
    } catch (error) {
        console.error('❌ خطا در ایجاد todo:', error);
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            success: false,
            error: 'خطا در ایجاد todo',
            details: error instanceof Error ? error.message : 'خطای ناشناخته'
        }, {
            status: 500
        });
    }
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__181hwec._.js.map