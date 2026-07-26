# سرویس‌های API - مستندات

سرویس‌های API برای ارتباط با backend و مدیریت داده‌ها طراحی شده‌اند. این سرویس‌ها از الگوهای طراحی مدرن و مدیریت خطا استفاده می‌کنند.

## 📡 فهرست سرویس‌ها

### ۱. MagicApiService
سرویس اصلی API با قابلیت retry خودکار و مدیریت خطا.

#### ویژگی‌ها
```typescript
interface MagicApiConfig {
  baseURL: string;
  timeout?: number;
  maxRetries?: number;
  retryDelay?: number;
}

interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

interface ApiError {
  message: string;
  code: string;
  status: number;
}
```

#### مثال استفاده
```typescript
import { MagicApiService } from '@/services/magic-api';

// ایجاد instance
const api = new MagicApiService({
  baseURL: 'https://api.example.com',
  maxRetries: 3,
  retryDelay: 1000,
});

// درخواست GET
async function fetchData() {
  try {
    const response = await api.get<DataType>('/endpoint');
    console.log('Data:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  }
}

// درخواست POST
async function postData(data: DataType) {
  try {
    const response = await api.post<ResponseType>('/endpoint', data);
    console.log('Response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  }
}
```

#### هوک useMagicApi
```tsx
import { useMagicApi } from '@/services/magic-api';

function ExampleComponent() {
  const { data, loading, error, retry } = useMagicApi<DataType>('/endpoint');

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>Data: {data?.name}</h1>
      <button onClick={retry}>Retry</button>
    </div>
  );
}
```

### ۲. SymbolService
سرویس مدیریت نمادها و داده‌های بازار.

#### متدها
```typescript
class SymbolService {
  // دریافت تمام نمادها
  async getAllSymbols(filters?: SymbolFilters): Promise<SymbolData[]>;
  
  // دریافت نماد بر اساس ID
  async getSymbolById(id: string): Promise<SymbolData | null>;
  
  // جستجوی نمادها
  async searchSymbols(query: string): Promise<SymbolData[]>;
  
  // دریافت داده‌های بازار
  async getMarketData(symbolId: string, period: string): Promise<MarketData[]>;
  
  // دریافت آمار بازار
  async getMarketStats(): Promise<MarketStats>;
  
  // دریافت نمادهای برتر
  async getTopSymbols(limit: number): Promise<SymbolData[]>;
}
```

#### مثال استفاده
```typescript
import { symbolService } from '@/services/symbol-service';

// دریافت تمام نمادها
async function loadSymbols() {
  const symbols = await symbolService.getAllSymbols({
    market: 'tehran',
    sector: 'banking',
  });
  return symbols;
}

// دریافت داده‌های بازار
async function loadMarketData(symbolId: string) {
  const marketData = await symbolService.getMarketData(symbolId, '1d');
  return marketData;
}

// جستجوی نمادها
async function searchSymbols(query: string) {
  const results = await symbolService.searchSymbols(query);
  return results;
}
```

### ۳. ScoringService
سرویس محاسبه امتیازها و رتبه‌بندی.

#### متدها
```typescript
class ScoringService {
  // محاسبه امتیاز نماد
  async calculateSymbolScore(symbolId: string): Promise<SymbolScore>;
  
  // دریافت رتبه‌بندی
  async getRankings(filters?: RankingFilters): Promise<Ranking[]>;
  
  // دریافت آمار امتیازها
  async getScoreStats(): Promise<ScoreStats>;
  
  // مقایسه نمادها
  async compareSymbols(symbolIds: string[]): Promise<ComparisonResult>;
  
  // دریافت تاریخچه امتیاز
  async getScoreHistory(symbolId: string): Promise<ScoreHistory[]>;
}
```

#### مثال استفاده
```typescript
import { scoringService } from '@/services/scoring-service';

// محاسبه امتیاز
async function calculateScore(symbolId: string) {
  const score = await scoringService.calculateSymbolScore(symbolId);
  return score;
}

// دریافت رتبه‌بندی
async function loadRankings() {
  const rankings = await scoringService.getRankings({
    dimension: 'financial',
    limit: 10,
  });
  return rankings;
}

// مقایسه نمادها
async function compareSymbols(symbolIds: string[]) {
  const comparison = await scoringService.compareSymbols(symbolIds);
  return comparison;
}
```

### ۴. HierarchyService
سرویس مدیریت سلسله‌مراتب و ساختار داده.

#### متدها
```typescript
class HierarchyService {
  // دریافت ساختار سلسله‌مراتب
  async getHierarchyTree(): Promise<HierarchyNode>;
  
  // دریافت گره بر اساس ID
  async getNodeById(nodeId: string): Promise<HierarchyNode | null>;
  
  // جستجو در سلسله‌مراتب
  async searchNodes(query: string): Promise<HierarchyNode[]>;
  
  // دریافت فرزندان گره
  async getChildren(nodeId: string): Promise<HierarchyNode[]>;
  
  // دریافت والدین گره
  async getParents(nodeId: string): Promise<HierarchyNode[]>;
}
```

#### مثال استفاده
```typescript
import { hierarchyService } from '@/services/hierarchy-service';

// دریافت ساختار کامل
async function loadHierarchy() {
  const tree = await hierarchyService.getHierarchyTree();
  return tree;
}

// دریافت فرزندان
async function loadChildren(nodeId: string) {
  const children = await hierarchyService.getChildren(nodeId);
  return children;
}

// جستجو
async function searchHierarchy(query: string) {
  const results = await hierarchyService.searchNodes(query);
  return results;
}
```

## 🔧 الگوهای طراحی

### ۱. Retry Pattern
```typescript
async function fetchWithRetry<T>(
  url: string,
  options: RequestInit,
  maxRetries: number = 3,
  retryDelay: number = 1000
): Promise<T> {
  let lastError: Error;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      lastError = error as Error;
      
      // اگر آخرین تلاش نباشد، صبر کن
      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
        retryDelay *= 2; // Exponential backoff
      }
    }
  }
  
  throw lastError;
}
```

### ۲. Circuit Breaker Pattern
```typescript
class CircuitBreaker {
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private failureCount = 0;
  private lastFailureTime: number | null = null;
  private readonly threshold: number;
  private readonly resetTimeout: number;

  constructor(threshold: number = 5, resetTimeout: number = 60000) {
    this.threshold = threshold;
    this.resetTimeout = resetTimeout;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - (this.lastFailureTime || 0) > this.resetTimeout) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await fn();
      
      if (this.state === 'half-open') {
        this.state = 'closed';
        this.failureCount = 0;
      }
      
      return result;
    } catch (error) {
      this.failureCount++;
      this.lastFailureTime = Date.now();
      
      if (this.failureCount >= this.threshold) {
        this.state = 'open';
      }
      
      throw error;
    }
  }
}
```

### ۳. Cache Pattern
```typescript
class ApiCache {
  private cache = new Map<string, { data: any; timestamp: number }>();
  private readonly ttl: number;

  constructor(ttl: number = 60000) {
    this.ttl = ttl;
  }

  get<T>(key: string): T | null {
    const cached = this.cache.get(key);
    
    if (!cached) return null;
    
    if (Date.now() - cached.timestamp > this.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data as T;
  }

  set(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  delete(key: string): void {
    this.cache.delete(key);
  }

  clear(): void {
    this.cache.clear();
  }
}
```

## 🚀 مدیریت خطا

### ساختار خطا
```typescript
class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
    public details?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// انواع خطاها
const ERROR_CODES = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  NOT_FOUND: 'NOT_FOUND',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  SERVER_ERROR: 'SERVER_ERROR',
};
```

### مدیریت خطا در کامپوننت‌ها
```tsx
import { useErrorBoundary } from 'react-error-boundary';
import { useMagicApi } from '@/services/magic-api';

function DataComponent() {
  const { showBoundary } = useErrorBoundary();
  const { data, error } = useMagicApi<DataType>('/endpoint');

  useEffect(() => {
    if (error) {
      showBoundary(error);
    }
  }, [error, showBoundary]);

  if (!data) return <div>Loading...</div>;

  return (
    <div>
      <h1>{data.name}</h1>
      <p>{data.description}</p>
    </div>
  );
}
```

## 📊 Monitoring و Logging

### ساختار Logging
```typescript
interface LogEntry {
  timestamp: number;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  context?: any;
  error?: Error;
}

class ApiLogger {
  private logs: LogEntry[] = [];
  private readonly maxLogs: number;

  constructor(maxLogs: number = 1000) {
    this.maxLogs = maxLogs;
  }

  log(level: LogEntry['level'], message: string, context?: any, error?: Error) {
    const entry: LogEntry = {
      timestamp: Date.now(),
      level,
      message,
      context,
      error,
    };

    this.logs.push(entry);
    
    // حفظ حداکثر تعداد logها
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // همچنین به console log کن
    console[level](message, context, error);
  }

  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  clearLogs(): void {
    this.logs = [];
  }
}
```

### Performance Monitoring
```typescript
class PerformanceMonitor {
  private metrics = new Map<string, { start: number; end?: number }>();

  start(metricName: string): void {
    this.metrics.set(metricName, { start: Date.now() });
  }

  end(metricName: string): number {
    const metric = this.metrics.get(metricName);
    
    if (!metric) {
      throw new Error(`Metric ${metricName} not found`);
    }

    metric.end = Date.now();
    const duration = metric.end - metric.start;
    
    // Log performance metric
    console.log(`Performance: ${metricName} took ${duration}ms`);
    
    return duration;
  }

  getMetrics(): Map<string, number> {
    const result = new Map<string, number>();
    
    for (const [name, metric] of this.metrics.entries()) {
      if (metric.end) {
        result.set(name, metric.end - metric.start);
      }
    }
    
    return result;
  }
}
```

## 🔒 امنیت

### Headers امنیتی
```typescript
const SECURE_HEADERS = {
  'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
};

// اضافه کردن headers به تمام درخواست‌ها
api.setDefaultHeaders(SECURE_HEADERS);
```

### Rate Limiting
```typescript
class RateLimiter {
  private requests = new Map<string, number[]>();
  private readonly limit: number;
  private readonly windowMs: number;

  constructor(limit: number = 100, windowMs: number = 60000) {
    this.limit = limit;
    this.windowMs = windowMs;
  }

  check(key: string): boolean {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    
    let userRequests = this.requests.get(key) || [];
    
    // حذف requestهای قدیمی
    userRequests = userRequests.filter(time => time > windowStart);
    
    // بررسی limit
    if (userRequests.length >= this.limit) {
      return false;
    }
    
    // اضافه کردن request جدید
    userRequests.push(now);
    this.requests.set(key, userRequests);
    
    return true;
  }

  getRemaining(key: string): number {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    
    const userRequests = this.requests.get(key) || [];
    const recentRequests = userRequests.filter(time => time > windowStart);
    
    return Math.max(0, this.limit - recentRequests.length);
  }
}
```

## 🧪 Testing

### Unit Tests برای سرویس‌ها
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MagicApiService } from './magic-api';

describe('MagicApiService', () => {
  let api: MagicApiService;
  let mockFetch: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockFetch = vi.fn();
    global.fetch = mockFetch;
    
    api = new MagicApiService({
      baseURL: 'https://api.example.com',
    });
  });

  it('should make GET request', async () => {
    const mockResponse = { data: 'test' };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    const result = await api.get('/test');
    
    expect(result.data).toBe('test');
    expect(mockFetch).toHaveBeenCalledWith(
      'https://api.example.com/test',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('should handle errors', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    await expect(api.get('/test')).rejects.toThrow('HTTP 404: Not Found');
  });
});
```

### Integration Tests
```typescript
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { symbolService } from './symbol-service';

describe('SymbolService Integration', () => {
  beforeAll(() => {
    // Setup test database
  });

  afterAll(() => {
    // Cleanup test database
  });

  it('should fetch symbols from API', async () => {
    const symbols = await symbolService.getAllSymbols();
    
    expect(Array.isArray(symbols)).toBe(true);
    expect(symbols.length).toBeGreaterThan(0);
    
    if (symbols.length > 0) {
      expect(symbols[0]).toHaveProperty('id');
      expect(symbols[0]).toHaveProperty('name');
      expect(symbols[0]).toHaveProperty('symbol');
    }
  });

  it('should handle API errors gracefully', async () => {
    // Mock API failure
    vi.spyOn(global, 'fetch').mockRejectedValue(new Error('Network error'));
    
    await expect(symbolService.getAllSymbols()).rejects.toThrow('Network error');
  });
});
```

## 📚 منابع

### Best Practices
- [REST API Design Best Practices](https://restfulapi.net/)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)
- [Error Handling in APIs](https://www.moesif.com/blog/technical/api-design/Which-HTTP-Status-Code-To-Use-For-Every-CRUD-App/)

### Tools
- [Postman](https://www.postman.com/) - API testing
- [Swagger](https://swagger.io/) - API documentation
- [Insomnia](https://insomnia.rest/) - API client

### Patterns
- [Retry Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)
- [Circuit Breaker Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- [Cache-Aside Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)