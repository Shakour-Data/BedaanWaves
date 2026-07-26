# مستندات فنی پروژه Bedaan6D

## فهرست مطالب
1. [معرفی پروژه](#معرفی-پروژه)
2. [معماری سیستم](#معماری-سیستم)
3. [مدل داده‌ها](#مدل-داده‌ها)
4. [سرویس‌های اصلی](#سرویس‌های-اصلی)
5. [API Endpoints](#api-endpoints)
6. [سیستم امتیازدهی](#سیستم-امتیازدهی)
7. [تست‌ها](#تست‌ها)
8. [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
9. [توسعه و مشارکت](#توسعه-و-مشارکت)

## معرفی پروژه

**Bedaan6D** یک سیستم تحلیل هوشمند بازار بورس تهران است که بر اساس مدل ۶ بعدی طراحی شده است. این سیستم با استفاده از الگوریتم‌های پیشرفته مالی و داده‌های بازار، امتیازهای چندبعدی برای هر نماد بورسی محاسبه می‌کند.

### اهداف اصلی
- ارائه تحلیل جامع ۶ بعدی از نمادهای بورسی
- محاسبه امتیازهای وزنی بر اساس اهمیت هر بعد
- رتبه‌بندی نمادها بر اساس امتیازهای محاسبه شده
- ارائه داشبورد تعاملی برای تحلیل‌گران و سرمایه‌گذاران

### ساختار ۶ بعدی
1. **تحلیل تکنیکال (Technical Analysis)**
2. **تحلیل بنیادی (Fundamental Analysis)**
3. **تحلیل روانشناسی بازار (Market Psychology)**
4. **تحلیل کمی (Quantitative Analysis)**
5. **تحلیل صنعت (Industry Analysis)**
6. **تحلیل ریسک (Risk Analysis)**

هر بعد اصلی شامل ۶ زیربعد، هر زیربعد شامل ۷ جنبه، و هر جنبه شامل ۹ زیرمجموعه می‌باشد که در مجموع ۲۲۶۸ عنصر تحلیلی را تشکیل می‌دهند.

## معماری سیستم

### تکنولوژی‌های اصلی
- **فرانت‌اند**: Next.js 16 با React 19 و TypeScript
- **استایل‌ینگ**: Tailwind CSS با shadcn/ui
- **بک‌اند**: Next.js API Routes
- **دیتابیس**: PostgreSQL با Prisma ORM
- **تست**: Vitest (واحد) و Playwright (E2E)

### ساختار پوشه‌ها
```
Bedaan6D-project/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── api/               # API endpoints
│   │   │   └── 6d/           # API های سیستم ۶ بعدی
│   │   └── (pages)/          # صفحات فرانت‌اند
│   ├── components/            # کامپوننت‌های React
│   ├── lib/                   # کتابخانه‌ها و utilities
│   │   ├── db.ts             # اتصال به دیتابیس
│   │   ├── prisma.ts         # re-export برای backward compatibility
│   │   ├── hierarchy.ts      # توابع مدیریت سلسله‌مراتب
│   │   ├── scoring.ts        # الگوریتم‌های امتیازدهی
│   │   └── brs-client.ts     # کلاینت API بازار بورس
│   ├── services/             # سرویس‌های منطق کسب‌وکار
│   │   ├── hierarchy-service.ts
│   │   ├── symbol-service.ts
│   │   ├── scoring-service.ts
│   │   └── index.ts
│   └── test/                 # تست‌های واحد
├── prisma/                   # مدل‌های Prisma
│   ├── schema.prisma        # Schema اصلی
│   ├── seed.ts             # داده‌های اولیه
│   └── seed-simple.ts      # داده‌های ساده برای تست
├── __tests__/               # تست‌های یکپارچگی
│   ├── api/                # تست‌های API
│   └── services/           # تست‌های سرویس‌ها
├── docs/                   # مستندات
└── public/                 # فایل‌های استاتیک
```

### جریان داده‌ها
1. **دریافت داده‌های بازار** از BRS API یا fallback داخلی
2. **ذخیره‌سازی داده‌ها** در دیتابیس PostgreSQL
3. **محاسبه امتیازها** بر اساس ساختار ۶ بعدی
4. **ذخیره امتیازها** در دیتابیس برای تحلیل‌های آتی
5. **ارائه نتایج** از طریق API و داشبورد فرانت‌اند

## مدل داده‌ها

### مدل‌های اصلی Prisma

#### MainDimension (بعد اصلی)
```prisma
model MainDimension {
  id          String        @id @default(cuid())
  code        String        @unique  // مثال: TD-01
  name        String        // مثال: تحلیل تکنیکال
  description String?
  weight      Float         @default(1.0)
  order       Int           @unique
  createdAt   DateTime      @default(now())
  updatedAt   DateTime      @updatedAt
  
  // روابط
  subDimensions SubDimension[]
  scores        Score[]
  references    Reference[]
}
```

#### SubDimension (زیربعد)
```prisma
model SubDimension {
  id             String   @id @default(cuid())
  code           String   @unique  // مثال: TD-01-01
  name           String   // مثال: شاخص‌های روند
  description    String?
  weight         Float    @default(1.0)
  order          Int      @unique
  
  // روابط
  mainDimension   MainDimension @relation(fields: [mainDimensionId], references: [id])
  mainDimensionId String
  aspects         Aspect[]
  scores          Score[]
  references      Reference[]
}
```

#### Aspect (جنبه)
```prisma
model Aspect {
  id              String   @id @default(cuid())
  code            String   @unique  // مثال: TD-01-01-01
  name            String   // مثال: میانگین متحرک
  description     String?
  weight          Float    @default(1.0)
  order           Int      @unique
  
  // روابط
  subDimension     SubDimension @relation(fields: [subDimensionId], references: [id])
  subDimensionId   String
  subCategories    SubCategory[]
  scores           Score[]
  references       Reference[]
}
```

#### SubCategory (زیرمجموعه)
```prisma
model SubCategory {
  id          String   @id @default(cuid())
  code        String   @unique  // مثال: TD-01-01-01-01
  name        String   // مثال: MA-20
  description String?
  weight      Float    @default(1.0)
  order       Int      @unique
  
  // روابط
  aspect       Aspect @relation(fields: [aspectId], references: [id])
  aspectId     String
  scores       Score[]
  references   Reference[]
}
```

#### Symbol (نماد)
```prisma
model Symbol {
  id          String      @id @default(cuid())
  isin        String      @unique  // کد ISIN
  symbol      String      @unique  // نماد بورسی
  name        String      // نام شرکت
  market      String      // بازار: بورس، فرابورس، ...
  sector      String      // صنعت
  subSector   String?     // زیرصنعت
  createdAt   DateTime    @default(now())
  updatedAt   DateTime    @updatedAt
  
  // روابط
  marketData MarketData[]
  scores     Score[]
}
```

#### MarketData (داده‌های بازار)
```prisma
model MarketData {
  id                    String    @id @default(cuid())
  date                  DateTime
  price                 Float
  
  // شاخص‌های تکنیکال
  rsi                   Float?    // TA-01
  macd                  Float?    // TA-02
  bollingerUpper        Float?    // TA-03
  bollingerLower        Float?    // TA-04
  
  // شاخص‌های بنیادی
  peg                   Float?    // FA-04
  roe                   Float?    // FA-06
  debtToEquity          Float?    // FA-07
  
  // روابط
  symbol                Symbol    @relation(fields: [symbolId], references: [id])
  symbolId              String
  
  @@unique([symbolId, date])
}
```

#### Score (امتیاز)
```prisma
model Score {
  id                String      @id @default(cuid())
  value             Float       // امتیاز خام (0-100)
  weightedValue     Float       // امتیاز وزنی
  calculationDate   DateTime    @default(now())
  
  // روابط
  symbol            Symbol      @relation(fields: [symbolId], references: [id])
  symbolId          String
  
  mainDimension     MainDimension? @relation(fields: [mainDimensionId], references: [id])
  mainDimensionId   String?
  
  subDimension      SubDimension? @relation(fields: [subDimensionId], references: [id])
  subDimensionId    String?
  
  aspect            Aspect? @relation(fields: [aspectId], references: [id])
  aspectId          String?
  
  subCategory       SubCategory? @relation(fields: [subCategoryId], references: [id])
  subCategoryId     String?
  
  @@unique([symbolId, mainDimensionId, subDimensionId, aspectId, subCategoryId, calculationDate])
}
```

#### Reference (منبع علمی)
```prisma
model Reference {
  id              String    @id @default(cuid())
  title           String    // عنوان مقاله/کتاب
  authors         String    // نویسندگان
  year            Int       // سال انتشار
  journal         String?   // نام مجله
  doi             String?   // شناسه DOI
  url             String?   // لینک
  description     String?   // خلاصه
  
  // روابط
  mainDimension   MainDimension? @relation(fields: [mainDimensionId], references: [id])
  mainDimensionId String?
  
  subDimension    SubDimension? @relation(fields: [subDimensionId], references: [id])
  subDimensionId  String?
  
  aspect          Aspect? @relation(fields: [aspectId], references: [id])
  aspectId        String?
  
  subCategory     SubCategory? @relation(fields: [subCategoryId], references: [id])
  subCategoryId   String?
}
```

#### AuditLog (لاگ حسابرسی)
```prisma
model AuditLog {
  id          String    @id @default(cuid())
  action      String    // عملیات: CREATE, UPDATE, DELETE
  entity      String    // موجودیت: MainDimension, Symbol, ...
  entityId    String    // شناسه موجودیت
  userId      String?   // شناسه کاربر (اگر احراز هویت وجود داشته باشد)
  details     Json?     // جزئیات تغییرات
  ipAddress   String?   // آدرس IP
  userAgent   String?   // User Agent
  createdAt   DateTime  @default(now())
}
```

## سرویس‌های اصلی

### HierarchyService
مدیریت کامل ساختار سلسله‌مراتبی ۶ بعدی

#### متدهای اصلی
```typescript
class HierarchyService {
  // دریافت ساختار کامل سلسله‌مراتب
  async getFullHierarchy(): Promise<FullHierarchy>
  
  // ایجاد بعد اصلی جدید
  async createMainDimension(data: CreateMainDimensionInput): Promise<MainDimension>
  
  // دریافت بعد اصلی با شناسه
  async getMainDimension(id: string): Promise<MainDimension | null>
  
  // به‌روزرسانی بعد اصلی
  async updateMainDimension(id: string, data: UpdateMainDimensionInput): Promise<MainDimension>
  
  // حذف بعد اصلی
  async deleteMainDimension(id: string): Promise<MainDimension>
}
```

### SymbolService
مدیریت نمادها و داده‌های بازار

#### متدهای اصلی
```typescript
class SymbolService {
  // دریافت لیست نمادها با فیلتر
  async getSymbols(filters?: SymbolFilters): Promise<SymbolWithMarketData[]>
  
  // دریافت نماد با شناسه
  async getSymbol(id: string): Promise<SymbolWithMarketData | null>
  
  // ایجاد نماد جدید
  async createSymbol(data: CreateSymbolInput): Promise<Symbol>
  
  // به‌روزرسانی نماد
  async updateSymbol(id: string, data: UpdateSymbolInput): Promise<Symbol>
  
  // حذف نماد
  async deleteSymbol(id: string): Promise<Symbol>
  
  // افزودن داده‌های بازار برای نماد
  async addMarketData(symbolId: string, data: MarketDataInput): Promise<MarketData>
  
  // دریافت تعداد نمادها
  async getSymbolCount(filters?: SymbolFilters): Promise<number>
}
```

### ScoringService
سیستم امتیازدهی ۶ بعدی

#### متدهای اصلی
```typescript
class ScoringService {
  // محاسبه امتیاز برای نماد
  async calculateScores(input: ScoreCalculationInput): Promise<SymbolScoreSummary>
  
  // دریافت امتیازهای نماد
  async getSymbolScores(symbolId: string, startDate?: Date, endDate?: Date): Promise<Score[]>
  
  // دریافت رتبه‌بندی نمادها
  async getSymbolRankings(options?: RankingOptions): Promise<SymbolRanking[]>
  
  // دریافت آخرین امتیازهای همه نمادها
  async getLatestScores(dimensionId?: string): Promise<ScoreWithDimensionAndSymbol[]>
}
```

## API Endpoints

### مدیریت سلسله‌مراتب

#### `GET /api/6d/hierarchy`
دریافت ساختار کامل سلسله‌مراتبی

**پارامترها**: ندارد

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "mainDimensions": [
      {
        "id": "dim-1",
        "code": "TD-01",
        "name": "تحلیل تکنیکال",
        "weight": 1.0,
        "order": 1,
        "subDimensions": [...]
      }
    ]
  }
}
```

#### `POST /api/6d/hierarchy`
ایجاد بعد اصلی جدید

**بدنه درخواست**:
```json
{
  "code": "TD-02",
  "name": "تحلیل بنیادی",
  "description": "تحلیل بنیادی شرکت‌ها",
  "weight": 1.0,
  "order": 2
}
```

**پاسخ موفق** (201):
```json
{
  "success": true,
  "data": {
    "id": "dim-2",
    "code": "TD-02",
    "name": "تحلیل بنیادی",
    "weight": 1.0,
    "order": 2,
    "createdAt": "2024-01-01T00:00:00.000Z",
    "updatedAt": "2024-01-01T00:00:00.000Z"
  }
}
```

### مدیریت نمادها

#### `GET /api/6d/symbols`
دریافت لیست نمادها

**پارامترهای query**:
- `market` (اختیاری): فیلتر بر اساس بازار
- `sector` (اختیاری): فیلتر بر اساس صنعت
- `search` (اختیاری): جستجو در نماد و نام
- `page` (اختیاری): شماره صفحه (پیش‌فرض: 1)
- `limit` (اختیاری): تعداد در هر صفحه (پیش‌فرض: 20)

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "symbols": [
      {
        "id": "sym-1",
        "isin": "IRO1FOLD0001",
        "symbol": "فولاد",
        "name": "فولاد مبارکه اصفهان",
        "market": "بورس",
        "sector": "فلزات اساسی",
        "marketData": [...]
      }
    ],
    "pagination": {
      "total": 100,
      "page": 1,
      "limit": 20,
      "pages": 5
    }
  }
}
```

#### `POST /api/6d/symbols`
ایجاد نماد جدید

**بدنه درخواست**:
```json
{
  "isin": "IRO1FOLD0001",
  "symbol": "فولاد",
  "name": "فولاد مبارکه اصفهان",
  "market": "بورس",
  "sector": "فلزات اساسی",
  "subSector": "فولاد"
}
```

**پاسخ موفق** (201):
```json
{
  "success": true,
  "data": {
    "id": "sym-1",
    "isin": "IRO1FOLD0001",
    "symbol": "فولاد",
    "name": "فولاد مبارکه اصفهان",
    "market": "بورس",
    "sector": "فلزات اساسی",
    "createdAt": "2024-01-01T00:00:00.000Z",
    "updatedAt": "2024-01-01T00:00:00.000Z"
  }
}
```

### سیستم امتیازدهی

#### `POST /api/6d/scoring`
محاسبه امتیاز برای نماد

**بدنه درخواست**:
```json
{
  "symbolId": "sym-1",
  "date": "2024-01-01"
}
```

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "symbolId": "sym-1",
    "calculationDate": "2024-01-01T00:00:00.000Z",
    "dimensionScores": [
      {
        "dimensionId": "dim-1",
        "dimensionCode": "TD-01",
        "dimensionName": "تحلیل تکنیکال",
        "score": 85.5,
        "weightedScore": 85.5
      }
    ],
    "totalScore": 85.5,
    "totalWeightedScore": 85.5
  }
}
```

#### `GET /api/6d/scoring`
دریافت امتیازهای نماد

**پارامترهای query**:
- `symbolId` (الزامی): شناسه نماد
- `startDate` (اختیاری): تاریخ شروع
- `endDate` (اختیاری): تاریخ پایان
- `dimensionId` (اختیاری): فیلتر بر اساس بعد

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": [
    {
      "id": "score-1",
      "value": 85.5,
      "weightedValue": 85.5,
      "calculationDate": "2024-01-01T00:00:00.000Z",
      "mainDimension": {
        "id": "dim-1",
        "code": "TD-01",
        "name": "تحلیل تکنیکال"
      }
    }
  ]
}
```

### رتبه‌بندی

#### `GET /api/6d/scoring/rankings`
دریافت رتبه‌بندی نمادها

**پارامترهای query**:
- `dimensionId` (اختیاری): فیلتر بر اساس بعد
- `market` (اختیاری): فیلتر بر اساس بازار
- `sector` (اختیاری): فیلتر بر اساس صنعت
- `minScore` (اختیاری): حداقل امتیاز
- `maxScore` (اختیاری): حداکثر امتیاز
- `page` (اختیاری): شماره صفحه
- `limit` (اختیاری): تعداد در هر صفحه

**پاسخ موفق** (200):
```json
{
  "success": true,
  "data": {
    "rankings": [
      {
        "symbolId": "sym-1",
        "symbolCode": "فولاد",
        "symbolName": "فولاد مبارکه اصفهان",
        "score": 85.5,
        "weightedScore": 85.5,
        "rank": 1,
        "calculationDate": "2024-01-01T00:00:00.000Z"
      }
    ],
    "averageScore": 81.85,
    "pagination": {
      "total": 50,
      "page": 1,
      "limit": 20,
      "pages": 3
    }
  }
}
```

## سیستم امتیازدهی

### الگوریتم محاسبه امتیاز

#### ۱. جمع‌آوری داده‌ها
- دریافت آخرین داده‌های بازار برای نماد (۳۰ روز گذشته)
- تطبیق داده‌ها با ساختار سلسله‌مراتبی ۶ بعدی

#### ۲. محاسبه امتیاز خام
برای هر عنصر در سلسله‌مراتب:
```typescript
function calculateRawScore(element: HierarchyElement, marketData: MarketData): number {
  // استخراج شاخص مربوطه از داده‌های بازار
  const indicator = extractIndicator(element.code, marketData);
  
  // نرمال‌سازی شاخص به بازه ۰-۱۰۰
  const normalized = normalizeIndicator(indicator, element.code);
  
  // اعمال وزن عنصر
  return normalized * element.weight;
}
```

#### ۳. محاسبه امتیاز وزنی
```typescript
function calculateWeightedScore(rawScore: number, elementWeight: number, parentWeights: number[]): number {
  // محاسبه وزن کل (ضرب وزن‌های والدین)
  const totalWeight = elementWeight * parentWeights.reduce((a, b) => a * b, 1);
  
  // محاسبه امتیاز وزنی
  return rawScore * totalWeight;
}
```

#### ۴. تجمیع امتیازها
- جمع امتیازهای هر سطح برای محاسبه امتیاز سطح بالاتر
- محاسبه امتیاز نهایی نماد (میانگین وزنی امتیازهای ۶ بعد اصلی)

### فرمول‌های اصلی

#### نرمال‌سازی شاخص‌ها
```typescript
function normalizeRSI(rsi: number): number {
  // RSI بین ۰ تا ۱۰۰
  // نرمال‌سازی به بازه ۰-۱۰۰ با تمرکز بر بازه ۳۰-۷۰
  if (rsi < 30) return 0;
  if (rsi > 70) return 100;
  return (rsi - 30) * 2.5; // (rsi-30) * 100/(70-30)
}
```

#### محاسبه امتیاز نهایی
```typescript
function calculateFinalScore(dimensionScores: DimensionScore[]): number {
  const totalWeight = dimensionScores.reduce((sum, ds) => sum + ds.weight, 0);
  const weightedSum = dimensionScores.reduce((sum, ds) => sum + (ds.score * ds.weight), 0);
  
  return weightedSum / totalWeight;
}
```

## تست‌ها

### تست‌های واحد

#### پوشه `__tests__/services/`
- **hierarchy-service.test.ts**: تست‌های HierarchyService
- **symbol-service.test.ts**: تست‌های SymbolService  
- **scoring-service.test.ts**: تست‌های ScoringService

#### پوشه `src/test/`
- تست‌های کامپوننت‌های React
- تست‌های توابع utility
- تست‌های API routes موجود

### تست‌های یکپارچگی

#### پوشه `__tests__/api/`
- **hierarchy.test.ts**: تست‌های endpoint مدیریت سلسله‌مراتب
- **symbols.test.ts**: تست‌های endpoint مدیریت نمادها
- **scoring.test.ts**: تست‌های endpoint سیستم امتیازدهی
- **rankings.test.ts**: تست‌های endpoint رتبه‌بندی

### اجرای تست‌ها

```bash
# اجرای همه تست‌ها
npm test

# اجرای تست‌های واحد سرویس‌ها
npm test -- --run __tests__/services

# اجرای تست‌های یکپارچگی API
npm test -- --run __tests__/api

# اجرای تست با coverage
npm run test:coverage
```

## نصب و راه‌اندازی

### پیش‌نیازها
- Node.js 18 یا بالاتر
- PostgreSQL 14 یا بالاتر
- npm یا yarn

### مراحل نصب

#### ۱. کلون کردن پروژه
```bash
git clone <repository-url>
cd Bedaan6D-project
```

#### ۲. نصب وابستگی‌ها
```bash
npm install
```

#### ۳. تنظیم متغیرهای محیطی
فایل `.env.local` ایجاد کنید:
```env
DATABASE_URL="postgresql://username:password@localhost:5432/bedaan6d"
NODE_ENV="development"
```

#### ۴. راه‌اندازی دیتابیس
```bash
# اجرای migration
npx prisma migrate dev

# ایجاد داده‌های اولیه
npx prisma db seed
```

#### ۵. اجرای پروژه
```bash
# حالت توسعه
npm run dev

# ساخت برای تولید
npm run build

# اجرا در تولید
npm start
```

### تنظیمات دیتابیس

#### PostgreSQL
```sql
CREATE DATABASE bedaan6d;
CREATE USER bedaan_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE bedaan6d TO bedaan_user;
```

#### Prisma Migration
```bash
# ایجاد migration جدید
npx prisma migrate dev --name init

# اعمال migration‌های موجود
npx prisma migrate deploy

# مشاهده داده‌ها
npx prisma studio
```

## توسعه و مشارکت

### ساختار کد

#### استانداردهای کدنویسی
- استفاده از TypeScript با strict mode
- نام‌گذاری camelCase برای متغیرها و توابع
- نام‌گذاری PascalCase برای کلاس‌ها و اینترفیس‌ها
- استفاده از async/await برای عملیات ناهمزمان
- مدیریت خطا با try/catch و throw

#### الگوهای طراحی
- **Repository Pattern**: برای دسترسی به دیتابیس
- **Service Layer**: برای منطق کسب‌وکار
- **DTO Pattern**: برای انتقال داده‌ها بین لایه‌ها
- **Dependency Injection**: برای تست‌پذیری

### فرآیند توسعه

#### ۱. ایجاد feature جدید
```bash
# ایجاد branch جدید
git checkout -b feature/new-feature

# توسعه feature
# ...

# commit تغییرات
git add .
git commit -m "feat: اضافه کردن feature جدید"
```

#### ۲. اجرای تست‌ها
```bash
npm test
npm run lint
```

#### ۳. ایجاد pull request
- push branch به remote
- ایجاد pull request در GitHub
- بررسی کد توسط همکاران
- merge پس از تایید

### مستندسازی

#### مستندات کد
```typescript
/**
 * محاسبه امتیاز برای یک نماد
 * @param input - اطلاعات مورد نیاز برای محاسبه امتیاز
 * @returns خلاصه امتیازهای محاسبه شده
 * @throws {ValidationError} اگر داده‌های ورودی نامعتبر باشد
 * @throws {DatabaseError} اگر خطایی در دسترسی به دیتابیس رخ دهد
 */
async calculateScores(input: ScoreCalculationInput): Promise<SymbolScoreSummary> {
  // implementation
}
```

#### مستندات API
- استفاده از OpenAPI/Swagger
- مستندات در فایل `docs/API_DOCUMENTATION.md`
- مثال‌های درخواست و پاسخ

### بهینه‌سازی

#### عملکرد
- کش‌کردن داده‌های پرکاربرد
- استفاده از pagination برای لیست‌های بزرگ
- بهینه‌سازی queryهای دیتابیس
- lazy loading برای داده‌های سنگین

#### امنیت
- اعتبارسنجی ورودی‌ها
- escaping داده‌های خروجی
- محدود کردن rate limit
- logging عملیات حساس

### منابع علمی

#### مدل‌های مالی
1. **Fama-French Five-Factor Model** (2015)
2. **Capital Asset Pricing Model (CAPM)**
3. **Modern Portfolio Theory (MPT)**
4. **Black-Scholes Model**

#### تحلیل تکنیکال
1. **Moving Averages** (MA, EMA)
2. **Relative Strength Index (RSI)**
3. **Moving Average Convergence Divergence (MACD)**
4. **Bollinger Bands**

#### تحلیل بنیادی
1. **Price-to-Earnings Ratio (P/E)**
2. **Price/Earnings to Growth Ratio (PEG)**
3. **Return on Equity (ROE)**
4. **Debt-to-Equity Ratio**

### نکات مهم

#### مقیاس‌پذیری
- طراحی ماژولار برای اضافه کردن ابعاد جدید
- پشتیبانی از چندین بازار بورسی
- امکان اضافه کردن شاخص‌های تحلیلی جدید

#### قابلیت اطمینان
- fallback برای APIهای خارجی
- backup و recovery دیتابیس
- monitoring و alerting

#### کاربرپسندی
- رابط کاربری فارسی و RTL
- گزارش‌های قابل تنظیم
- export داده‌ها به فرمت‌های مختلف

---

**تاریخ آخرین به‌روزرسانی**: ۵ ژوئیه ۲۰۲۶  
**نگارنده**: تیم توسعه Bedaan6D  
**نسخه**: ۱.۰.۰