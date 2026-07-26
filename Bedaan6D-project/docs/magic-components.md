# کامپوننت‌های جادویی - مستندات

کامپوننت‌های جادویی بر اساس اصول عددشناسی، کابالا و NLP طراحی شده‌اند. این کامپوننت‌ها سیستم طراحی یکپارچه‌ای را ایجاد می‌کنند که هم زیبایی‌شناختی و هم عملکردی است.

## 📦 فهرست کامپوننت‌ها

### ۱. MagicButton
دکمه جادویی با افکت glow و قانون ۳-۷-۳ انیمیشن.

#### ویژگی‌ها
```typescript
interface MagicButtonProps {
  variant?: 'fire' | 'water' | 'earth' | 'air';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  children: React.ReactNode;
  className?: string;
}
```

#### مثال استفاده
```tsx
import { MagicButton } from '@/components/magic/MagicButton';

function Example() {
  return (
    <div>
      <MagicButton variant="fire" size="lg">
        دکمه آتشین
      </MagicButton>
      
      <MagicButton variant="water" loading>
        در حال بارگذاری...
      </MagicButton>
      
      <MagicButton variant="air" icon={<Sparkles />} iconPosition="right">
        دکمه هوایی
      </MagicButton>
    </div>
  );
}
```

#### Variantها
- **fire**: رنگ قرمز، افکت glow قرمز، برای actions مهم
- **water**: رنگ آبی، افکت موج، برای actions آرام
- **earth**: رنگ خاکستری، افکت سایه، برای actions خنثی
- **air**: رنگ طلایی، افکت درخشش، برای actions الهام‌بخش

### ۲. MagicCard
کارت جادویی با سایه‌های رنگ‌شده و انیمیشن‌های ظریف.

#### ویژگی‌ها
```typescript
interface MagicCardProps {
  variant?: 'fire' | 'water' | 'earth' | 'air';
  elevation?: 'sm' | 'md' | 'lg' | 'xl';
  hoverable?: boolean;
  children: React.ReactNode;
  className?: string;
}
```

#### مثال استفاده
```tsx
import { MagicCard } from '@/components/magic/MagicCard';

function Example() {
  return (
    <MagicCard variant="water" elevation="lg" hoverable>
      <h3>عنوان کارت</h3>
      <p>محتوا و توضیحات کارت</p>
    </MagicCard>
  );
}
```

### ۳. MagicForm
سیستم فرم جادویی با validation و انیمیشن‌های تعاملی.

#### کامپوننت‌های فرم
- **MagicInput**: فیلد ورودی با validation
- **MagicTextarea**: فیلد متن با validation
- **MagicSelect**: dropdown با validation
- **MagicCheckbox**: checkbox با validation
- **MagicRadio**: radio button با validation

#### مثال استفاده
```tsx
import { MagicForm, MagicInput, MagicTextarea } from '@/components/magic/MagicForm';

function ExampleForm() {
  const handleSubmit = (data: FormData) => {
    console.log('Form data:', data);
  };

  return (
    <MagicForm onSubmit={handleSubmit}>
      <MagicInput
        name="username"
        label="نام کاربری"
        variant="fire"
        required
        validation={{
          minLength: 3,
          maxLength: 20,
          pattern: /^[a-zA-Z0-9_]+$/,
        }}
      />
      
      <MagicTextarea
        name="description"
        label="توضیحات"
        variant="water"
        rows={4}
      />
      
      <button type="submit">ارسال</button>
    </MagicForm>
  );
}
```

### ۴. MagicGrid
سیستم grid جادویی بر اساس عدد ۱۲ برای کمال فضایی.

#### کامپوننت‌های Grid
- **MagicContainer**: container اصلی
- **MagicRow**: ردیف grid
- **MagicColumn**: ستون grid
- **MagicGridSystem**: سیستم grid کامل
- **MagicSpacer**: فضای خالی responsive
- **MagicDivider**: جداکننده با رنگ‌های عناصر

#### مثال استفاده
```tsx
import { MagicGridSystem, MagicRow, MagicColumn } from '@/components/magic/MagicGrid';

function ExampleGrid() {
  return (
    <MagicGridSystem>
      <MagicRow gap="md">
        <MagicColumn span={4}>
          <div>ستون ۱ (۴ از ۱۲)</div>
        </MagicColumn>
        <MagicColumn span={8}>
          <div>ستون ۲ (۸ از ۱۲)</div>
        </MagicColumn>
      </MagicRow>
      
      <MagicRow gap="lg">
        <MagicColumn span={{ base: 12, md: 6, lg: 3 }}>
          <div>ستون responsive</div>
        </MagicColumn>
        <MagicColumn span={{ base: 12, md: 6, lg: 3 }}>
          <div>ستون responsive</div>
        </MagicColumn>
        <MagicColumn span={{ base: 12, md: 6, lg: 3 }}>
          <div>ستون responsive</div>
        </MagicColumn>
        <MagicColumn span={{ base: 12, md: 6, lg: 3 }}>
          <div>ستون responsive</div>
        </MagicColumn>
      </MagicRow>
    </MagicGridSystem>
  );
}
```

### ۵. MagicTypography
سیستم تایپوگرافی جادویی بر اساس دنباله فیبوناچی.

#### ویژگی‌ها
```typescript
interface MagicTypographyProps {
  variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 
            'bodyLg' | 'bodyMd' | 'bodySm' | 'bodyXs' |
            'link' | 'highlight' | 'error' | 'success' | 'warning';
  element?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'p' | 'span' | 'div';
  gradient?: 'fire' | 'water' | 'air' | 'earth';
  children: React.ReactNode;
  className?: string;
}
```

#### مثال استفاده
```tsx
import { MagicTypography } from '@/components/magic/MagicTypography';

function ExampleTypography() {
  return (
    <div>
      <MagicTypography variant="h1" gradient="fire">
        عنوان اصلی
      </MagicTypography>
      
      <MagicTypography variant="bodyMd">
        متن معمولی با سایز متوسط
      </MagicTypography>
      
      <MagicTypography variant="link" element="a" href="#">
        لینک جادویی
      </MagicTypography>
    </div>
  );
}
```

## 🎨 اصول طراحی

### ۱. قانون ۳-۷-۳ انیمیشن
- **۳۰۰ms**: انیمیشن‌های سریع (hover, focus)
- **۷۰۰ms**: انیمیشن‌های متوسط (transitions)
- **۳۰۰۰ms**: انیمیشن‌های آهسته (background effects)

### ۲. روانشناسی رنگ کابالایی
```typescript
const COLOR_PSYCHOLOGY = {
  fire: {
    color: '#C62828',
    emotion: 'انرژی، عمل، اشتیاق',
    usage: 'دکمه‌های مهم، alerts، calls-to-action'
  },
  water: {
    color: '#1565C0',
    emotion: 'آرامش، شهود، ارتباط',
    usage: 'فرم‌ها، اطلاعات، navigation'
  },
  earth: {
    color: '#F5F5F5',
    emotion: 'ثبات، امنیت، واقع‌گرایی',
    usage: 'backgrounds، cards خنثی'
  },
  air: {
    color: '#FFD54F',
    emotion: 'روشنایی، خلاقیت، الهام',
    usage: 'highlights، accents، special features'
  }
};
```

### ۳. سلسله‌مراتب فیبوناچی
```typescript
function calculateHierarchyFontSize(level: number): string {
  const baseSize = 16; // 1rem
  const goldenMultiplier = Math.pow(1.618, level);
  const calculatedSize = baseSize * goldenMultiplier;
  
  // گرد کردن به نزدیکترین عدد فیبوناچی
  const fibonacciSizes = [8, 13, 21, 34, 55, 89];
  const closestSize = fibonacciSizes.reduce((prev, curr) => {
    return Math.abs(curr - calculatedSize) < Math.abs(prev - calculatedSize) ? curr : prev;
  });
  
  return `${closestSize}px`;
}
```

## 🔧 Customization

### Override Styles
```tsx
// استفاده از className
<MagicButton className="custom-class">دکمه</MagicButton>

// استفاده از style
<MagicCard style={{ backgroundColor: 'var(--custom-color)' }}>
  محتوا
</MagicCard>
```

### Extend Components
```tsx
import { MagicButton, type MagicButtonProps } from '@/components/magic/MagicButton';

interface ExtendedButtonProps extends MagicButtonProps {
  customProp?: string;
}

function ExtendedButton({ customProp, ...props }: ExtendedButtonProps) {
  return (
    <MagicButton {...props}>
      {props.children}
      {customProp && <span>{customProp}</span>}
    </MagicButton>
  );
}
```

## 🧪 Testing

### Unit Tests
```typescript
// MagicButton.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { MagicButton } from './MagicButton';

describe('MagicButton', () => {
  it('renders children correctly', () => {
    render(<MagicButton>Click me</MagicButton>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<MagicButton onClick={handleClick}>Click me</MagicButton>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Accessibility Tests
```typescript
import { render } from '@testing-library/react';
import { axe } from 'jest-axe';
import { MagicButton } from './MagicButton';

describe('MagicButton accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<MagicButton>Accessible button</MagicButton>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

## 📚 منابع و الهامات

### عددشناسی
- عدد ۱۲: کمال فضایی در طراحی
- نسبت طلایی (۱.۶۱۸): تناسب زیبایی‌شناختی
- دنباله فیبوناچی: رشد ارگانیک

### کابالا
- چهار عنصر: آتش، آب، خاک، هوا
- روانشناسی رنگ: تأثیر رنگ‌ها بر احساسات
- انرژی: سطح انرژی کاربر و تعامل

### NLP (برنامه‌نویسی عصبی-زبانی)
- Patterns: الگوهای تعامل کاربر
- States: حالت‌های ذهنی کاربر
- Anchoring: ایجاد ارتباط‌های مثبت

## 🚀 بهترین روش‌ها

### ۱. Consistency
- از variantهای استاندارد استفاده کنید
- از spacingهای فیبوناچی پیروی کنید
- از قانون ۳-۷-۳ برای انیمیشن‌ها استفاده کنید

### ۲. Accessibility
- contrast ratio مناسب
- keyboard navigation
- screen reader support

### ۳. Performance
- lazy loading
- code splitting
- optimized animations

### ۴. Maintainability
- documentation
- tests
- clear naming conventions