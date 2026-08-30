# BedaanWaves Design System

A unified, financial-grade UI system for the BedaanWaves market analysis platform. All components share a single visual DNA built on CSS custom properties and Tailwind CSS v4.

## 1. Design Tokens

### Color Palette

All colors are defined as CSS custom properties in `globals.css` and exported from `styles/design-tokens.ts`.

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--color-primary` | `#005A9C` | `#3B82F6` | Primary CTAs, active states, links |
| `--color-primary-hover` | `#004578` | `#60A5FA` | Primary hover state |
| `--color-primary-light` | `#E6F0FA` | `#1E3A5F` | Primary tint backgrounds |
| `--color-secondary` | `#64748B` | `#94A3B8` | Secondary text, muted elements |
| `--color-success` | `#22C55E` | `#4ADE80` | Gains, positive indicators |
| `--color-warning` | `#F59E0B` | `#FBBF24` | Warnings, neutral/hold signals |
| `--color-error` | `#EF4444` | `#F87171` | Losses, errors, destructive actions |
| `--color-background` | `#F8FAFC` | `#0F172A` | Page background |
| `--color-surface` | `#FFFFFF` | `#1E293B` | Cards, elevated surfaces |
| `--color-surface-elevated` | `#FFFFFF` | `#334155` | Modals, dropdowns |
| `--color-neutral` | `#F8FAFC` | `#0F172A` | Neutral backgrounds |
| `--color-muted` | `#F1F5F9` | `#1E293B` | Subtle backgrounds |
| `--color-foreground` | `#0F172A` | `#F8FAFC` | Primary text |
| `--color-text-primary` | `#0F172A` | `#F8FAFC` | Primary text |
| `--color-text-secondary` | `#475569` | `#94A3B8` | Secondary text |
| `--color-text-muted` | `#94A3B8` | `#64748B` | Muted text |
| `--color-muted-foreground` | `#475569` | `#94A3B8` | Muted text (alias) |
| `--color-border` | `#E2E8F0` | `#334155` | Borders |
| `--color-border-light` | `#F1F5F9` | `#1E293B` | Subtle borders |

### Typography

| Property | Value |
|----------|-------|
| Font Family | `Inter`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, sans-serif |
| Font Mono | `JetBrains Mono`, `Fira Code`, monospace |
| Font Smoothing | Antialiased |

Font sizes use Tailwind's default scale (`text-xs` through `text-4xl`).

### Spacing

Consistent spacing scale (Tailwind default):
- `1` = 0.25rem (4px)
- `2` = 0.5rem (8px)
- `3` = 0.75rem (12px)
- `4` = 1rem (16px)
- `5` = 1.5rem (24px)
- `6` = 2rem (32px)
- `8` = 3rem (48px)
- `10` = 4rem (64px)

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 0.25rem (4px) | Small badges, inputs |
| `--radius-md` | 0.5rem (8px) | Buttons, cards |
| `--radius-lg` | 0.75rem (12px) | Large cards |
| `--radius-xl` | 1rem (16px) | Modals, dropdowns |
| `--radius-2xl` | 1.5rem (24px) | Large containers |

### Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | Subtle depth |
| `--shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1)` | Cards, dropdowns |
| `--shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1)` | Modals, popovers |
| `--shadow-xl` | `0 20px 25px -5px rgb(0 0 0 / 0.1)` | Overlays |

### Layout

| Token | Value | Usage |
|-------|-------|-------|
| `--max-width` | 80rem (1280px) | Container max-width |
| `--sidebar-width` | 16rem (256px) | Sidebar width |
| `--header-height` | 4rem (64px) | Topbar height |

---

## 2. Component Library

### Button

**File:** `src/components/ui/Button.tsx`

| Variant | Classes | Usage |
|---------|---------|-------|
| `primary` | `bg-primary text-white hover:bg-primary-hover` | Main CTAs |
| `secondary` | `bg-secondary text-white hover:bg-secondary/90` | Secondary actions |
| `outline` | `border-2 border-primary text-primary hover:bg-primary-light` | Tertiary actions |
| `ghost` | `text-foreground hover:bg-neutral` | Subtle actions |
| `destructive` | `bg-error text-white hover:bg-error/90` | Destructive actions |

| Size | Height | Padding | Font |
|------|--------|---------|------|
| `sm` | 2rem (32px) | px-3 | text-xs |
| `md` | 2.5rem (40px) | px-4 | text-sm |
| `lg` | 3rem (48px) | px-6 | text-base |

All buttons include:
- `focus:ring-2 focus:ring-primary/30 focus:ring-offset-2`
- `active:scale-[0.98]`
- `disabled:pointer-events-none disabled:opacity-60`
- `transition-all duration-200`

### Card

**File:** `src/components/ui/Card.tsx`

```tsx
<Card title="Card Title" subtitle="Optional subtitle" footer={<div>Footer actions</div>} hoverable>
  Card content
</Card>
```

- Border: `border-border`
- Background: `bg-surface`
- Radius: `rounded-xl`
- Shadow: `shadow-sm` → `shadow-md` on hover
- Header has `border-b border-border`
- Footer has `border-t border-border`

### Input

**File:** `src/components/ui/input.tsx`

```tsx
<Input placeholder="Enter text..." error helperText="Error message" />
```

- Height: `h-10`
- Border: `border-border`
- Background: `bg-surface`
- Focus: `focus:border-primary focus:ring-2 focus:ring-primary/20`
- Error state: `border-error focus:ring-error/20`
- Radius: `rounded-xl`

### Table

**File:** `src/components/ui/Table.tsx`

```tsx
<Table>
  <TableHeader>
    <TableHead>Column</TableHead>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>Data</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

- Header: `border-b border-border text-muted-foreground text-xs uppercase tracking-wider`
- Body: `divide-y divide-border`
- Row hover: `hover:bg-neutral/50`

### Modal

**File:** `src/components/ui/Modal.tsx`

```tsx
<Modal isOpen={open} onClose={() => setOpen(false)} title="Title" size="md">
  Modal content
</Modal>
```

- Sizes: `sm` (max-w-sm), `md` (max-w-md), `lg` (max-w-lg), `xl` (max-w-xl)
- Overlay: `bg-black/40 backdrop-blur-sm`
- Animation: `animate-in fade-in zoom-in-95`
- Close button: top-right, `hover:bg-neutral`

### Toast

**File:** `src/components/ui/Toast.tsx`

```tsx
const { addToast } = useToast();
addToast({ type: "success", message: "Saved!", description: "Your changes have been saved." });
```

| Type | Border | Background | Text |
|------|--------|------------|------|
| `success` | `border-success/30` | `bg-success/5` | `text-success` |
| `error` | `border-error/30` | `bg-error/5` | `text-error` |
| `warning` | `border-warning/30` | `bg-warning/5` | `text-warning` |
| `info` | `border-primary/30` | `bg-primary-light/50` | `text-primary` |

### Badge

**File:** `src/components/ui/Badge.tsx`

```tsx
<Badge variant="success" size="sm">Label</Badge>
```

| Variant | Background | Text | Border |
|---------|------------|------|--------|
| `default` | `bg-primary/10` | `text-primary` | `border-primary/20` |
| `success` | `bg-success/10` | `text-success` | `border-success/20` |
| `error` | `bg-error/10` | `text-error` | `border-error/20` |
| `warning` | `bg-warning/10` | `text-warning` | `border-warning/20` |
| `info` | `bg-primary-light/50` | `text-primary` | `border-primary/20` |
| `neutral` | `bg-neutral` | `text-muted-foreground` | `border-border` |

### Spinner

**File:** `src/components/ui/Spinner.tsx`

```tsx
<Spinner size="md" />
```

- `sm`: `h-4 w-4 border-2`
- `md`: `h-8 w-8 border-3`
- `lg`: `h-12 w-12 border-4`
- Animation: `animate-spin`
- Border color: `border-solid border-border border-t-primary`

### Skeleton

**File:** `src/components/ui/Skeleton.tsx`

```tsx
<Skeleton className="h-4 w-32" />
```

- Uses `animate-pulse` with `bg-border`

### Progress Bar

**File:** `src/components/ui/ProgressBar.tsx`

```tsx
<ProgressBar currentStep={2} totalSteps={5} stepLabels={["Step 1", "Step 2", ...]} />
```

- Track: `bg-border`
- Fill: `bg-primary`
- Steps: completed = `bg-success`, active = `bg-primary ring-2 ring-primary/20`, pending = `bg-border`

### Error Message

**File:** `src/components/ui/ErrorMessage.tsx`

```tsx
<ErrorMessage message="Something went wrong" actions={[{ label: "Retry", onAction: () => {} }]} />
```

- Border: `border-error/20`
- Background: `bg-error/5`
- Icon: `text-error`
- Actions use `Button` with `variant="outline"`

---

## 3. Layout Components

### NewDashboardShell

**File:** `src/components/layout/NewDashboardShell.tsx`

Wraps all authenticated pages with:
- Fixed `NewSidebar` (left, hidden on mobile)
- Fixed `NewTopbar` (top)
- Centered `<main>` with `.container-grid`

### NewSidebar

**File:** `src/components/layout/NewSidebar.tsx`

- Width: `w-64`, hidden on mobile (`lg:block`)
- Active item: `bg-primary/10 text-primary`
- Logo: `bg-primary text-white rounded-lg`
- Bottom nav for Settings/Help

### NewTopbar

**File:** `src/components/layout/NewTopbar.tsx`

- Height: `h-16`, fixed top, `border-b border-border`
- Search input: `h-10 rounded-lg border-border`
- Notifications dropdown: `rounded-xl border-border shadow-lg`
- User menu: avatar with `bg-primary/10 text-primary`

### PublicLayout

**File:** `src/components/layout/PublicLayout.tsx`

- Sticky header with `backdrop-blur-xl`
- Footer with 4-column grid on desktop

---

## 4. Stock Search Bar

**File:** `src/components/search/StockSearchBar.tsx`

- Input height: `h-10`
- Border: `border-border`, focus `border-primary ring-2 ring-primary/20`
- Dropdown: `rounded-b-xl border-border shadow-lg`
- Active item: `bg-primary/10`
- Price change: `text-success` / `text-error`
- Loading: `animate-spin text-primary`

---

## 5. Financial Data Colors

For financial data visualization, use the semantic colors:

| Data State | Color Token | Tailwind Class |
|------------|-------------|----------------|
| Gain / Positive | `--color-success` | `text-success`, `bg-success` |
| Loss / Negative | `--color-error` | `text-error`, `bg-error` |
| Neutral / Hold | `--color-warning` | `text-warning`, `bg-warning` |
| Primary / Buy | `--color-primary` | `text-primary`, `bg-primary` |

Avoid hardcoded hex values in pages. Use the token classes above.

---

## 6. Dark Mode

Dark mode is toggled by adding/removing the `.dark` class on `<html>`.

- Managed by `ThemeProvider` and `useAppStore`
- Default theme: `dark`
- All colors automatically switch via CSS custom properties
- No component-level theme logic required

---

## 7. File Structure

```
frontend/src/
├── app/
│   └── globals.css          # Design tokens (@theme), base styles, animations
├── components/
│   ├── ui/
│   │   ├── Button.tsx       # Unified button
│   │   ├── Card.tsx         # Unified card
│   │   ├── Input.tsx        # Unified input
│   │   ├── Table.tsx        # Unified table
│   │   ├── Modal.tsx        # Unified modal
│   │   ├── Toast.tsx        # Toast notifications
│   │   ├── Badge.tsx        # Status badges
│   │   ├── Spinner.tsx      # Loading spinner
│   │   ├── Skeleton.tsx     # Skeleton loader
│   │   ├── ProgressBar.tsx  # Progress indicator
│   │   ├── ErrorMessage.tsx # Error alerts
│   │   └── TarotCard.tsx    # Backward-compatible card wrapper
│   ├── layout/
│   │   ├── NewDashboardShell.tsx
│   │   ├── NewSidebar.tsx
│   │   ├── NewTopbar.tsx
│   │   └── PublicLayout.tsx
│   └── search/
│       └── StockSearchBar.tsx
├── styles/
│   ├── design-tokens.ts     # TypeScript design tokens
│   └── design-system.css    # (removed - superseded by globals.css)
└── lib/
    └── cn.ts               # Class name utility
```

---

## 8. Migration Notes

### Before → After

| Before | After |
|--------|-------|
| `bg-red-600` | `bg-error` |
| `text-red-600` | `text-error` |
| `text-green-600` | `text-success` |
| `bg-[var(--color-primary)]/10` | `bg-primary/10` |
| `border-[var(--color-border)]` | `border-border` |
| `hover:bg-red-700` | `hover:bg-error/90` |
| `PrimaryButton` | `Button` (backward-compatible re-export) |
| `TarotCard` | `Card` (backward-compatible re-export) |

### CSS Custom Properties → Tailwind Classes

Use Tailwind utility classes instead of `var()` expressions:
- ❌ `bg-[var(--color-surface)]`
- ✅ `bg-surface`
- ❌ `text-[var(--color-text-primary)]`
- ✅ `text-foreground`
- ❌ `border-[var(--color-border)]`
- ✅ `border-border`

---

## 9. QA Checklist

- [ ] All primary buttons use `Button` component with `variant="primary"`
- [ ] All cards use `Card` component with consistent padding/shadow
- [ ] All inputs use `Input` component with consistent height/focus styles
- [ ] Search bar dropdown matches global dropdown styling
- [ ] No stray hardcoded HEX values in components
- [ ] Spacing uses consistent scale (4px grid)
- [ ] Border radius uses scale tokens (`rounded-lg`, `rounded-xl`)
- [ ] Shadows use scale tokens (`shadow-sm`, `shadow-md`)
- [ ] Dark mode toggles all components correctly
- [ ] Responsive layout works on mobile, tablet, desktop
- [ ] All tables use `Table` component with consistent header/body styling
- [ ] All badges use `Badge` component with semantic variants
- [ ] All modals use `Modal` component with consistent animation
- [ ] All toasts use `Toast` component with semantic variants
