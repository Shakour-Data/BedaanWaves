# Design System Audit Checklist

Use this checklist to audit any existing UI against the standard, beautiful, and universal design system.

## 1. Design Philosophy
- [ ] Interface is clean and minimalist with no visual clutter
- [ ] Every element serves a clear purpose
- [ ] Consistent across the entire application
- [ ] Emotionally pleasant with proper spacing, color, and typography
- [ ] Adaptive and responsive on all screen sizes

## 2. Global Visual Foundation

### 2.1 Color Palette
- [ ] Uses exact HEX values from the specification
- [ ] Primary: #2563EB
- [ ] Primary Hover: #1D4ED8
- [ ] Secondary: #64748B
- [ ] Success: #22C55E
- [ ] Warning: #F59E0B
- [ ] Error: #EF4444
- [ ] Background: #F8FAFC
- [ ] Surface: #FFFFFF
- [ ] Text Primary: #0F172A
- [ ] Text Secondary: #475569
- [ ] Border: #E2E8F0
- [ ] No pure black (#000) for text
- [ ] No pure white (#FFF) on bright backgrounds without contrast check

### 2.2 Typography System
- [ ] Font family: Inter or system fallback
- [ ] Base font size: 16px (1rem) on desktop
- [ ] Never smaller than 14px on any device
- [ ] Modular scale 1.25 applied
- [ ] H1: 2.5rem / 700 / 1.2
- [ ] H2: 2.0rem / 600 / 1.3
- [ ] H3: 1.5rem / 600 / 1.4
- [ ] H4: 1.25rem / 600 / 1.4
- [ ] Body: 1.0rem / 400 / 1.6
- [ ] Small: 0.875rem / 400 / 1.5
- [ ] Caption: 0.75rem / 400 / 1.4
- [ ] Body text max 75 characters per line
- [ ] No more than 3 different font families

### 2.3 Spacing System
- [ ] All spacing is multiples of 8px (0.5rem)
- [ ] xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 32px, 2xl: 48px, 3xl: 64px

### 2.4 Border Radius
- [ ] Small: 4px (inputs, small buttons)
- [ ] Medium: 8px (cards, modals, default buttons)
- [ ] Large: 12px (containers, panels)
- [ ] Full: 9999px (pill badges, avatars)

### 2.5 Shadows
- [ ] None: 0
- [ ] Sm: 0 1px 2px rgba(0,0,0,0.05)
- [ ] Md: 0 4px 6px rgba(0,0,0,0.07)
- [ ] Lg: 0 10px 25px rgba(0,0,0,0.10)
- [ ] Xl: 0 20px 50px rgba(0,0,0,0.15)

## 3. Core UI Components

### 3.1 Buttons
- [ ] Height: 40px (md), 48px (lg)
- [ ] Padding: 16px horizontal minimum
- [ ] Variants: Primary, Secondary, Ghost, Destructive
- [ ] States: Default, Hover, Active, Disabled (opacity 0.5)
- [ ] Loading spinner state with "Processing..." text
- [ ] Transitions: 150ms ease-out

### 3.2 Input Fields
- [ ] Height: 40px (text inputs), auto for textarea (min-height: 80px)
- [ ] Border: 1px solid Border color, rounded-md
- [ ] Padding: 8px 12px
- [ ] Label: positioned above, bold (600), size sm, margin-bottom: 4px
- [ ] Placeholder: Text Secondary color
- [ ] Focus: 2px Primary color ring, no outline
- [ ] Error state: Error border + error message below
- [ ] Success state: Success border + check icon

### 3.3 Cards
- [ ] Background: Surface color
- [ ] Border: 1px solid Border color (optional)
- [ ] Border Radius: md (8px)
- [ ] Padding: 24px
- [ ] Shadow: md by default
- [ ] Structure: Header, Body, Footer with consistent spacing

### 3.4 Modals / Dialogs
- [ ] Overlay: rgba(0,0,0,0.5) with backdrop-blur-sm
- [ ] Position: Centered vertically + horizontally
- [ ] Max Width: 480px (sm), 640px (md), 896px (lg)
- [ ] Padding: 32px
- [ ] Close button: "X" icon in top-right corner
- [ ] Actions: Cancel (Ghost) + Confirm (Primary) buttons

### 3.5 Navigation
- [ ] Top Navbar height: 64px
- [ ] Background: Surface or transparent with blur
- [ ] Logo on left, actions on right
- [ ] Sticky top with shadow-sm on scroll
- [ ] Sidebar width: 240px (collapsible to 64px)
- [ ] Active item highlighted with Primary bg or left border

### 3.6 Tables / Data Grids
- [ ] Header: Bold, Text Secondary, background light
- [ ] Rows: Hover with subtle Background color change
- [ ] Borders: Horizontal lines only (Border color)
- [ ] Padding: 12px 16px per cell
- [ ] Empty state: "No data" with illustration

### 3.7 Alerts / Toasts
- [ ] Position: Top-right for toasts, inline for alerts
- [ ] 4 Types: Info, Success, Warning, Error
- [ ] Structure: Icon + Message + Close button
- [ ] Timeout: 5 seconds for toasts
- [ ] Inline alerts: Full width, rounded-md, padding 16px

### 3.8 Badges / Tags
- [ ] Sizes: sm (20px), md (24px)
- [ ] Variants: Primary, Success, Warning, Error, Neutral
- [ ] Rounded: Full (pill shape)

## 4. Layout Grid System
- [ ] 12-column fluid grid
- [ ] Gap: 16px (md) or 24px (lg)
- [ ] Container: Max-width 1280px, centered
- [ ] Breakpoints: sm 640px, md 768px, lg 1024px, xl 1280px, 2xl 1536px

## 5. Micro-Interactions
- [ ] Hover: 150ms ease-out
- [ ] Modal: 200ms ease-in-out
- [ ] Dropdown: 200ms ease-out
- [ ] Page transitions: 300ms ease-in-out
- [ ] Loading skeletons: pulse animation (1.5s loop)

## 6. Typography & Content Rules
- [ ] Headings start with H1 at top of each page
- [ ] Line length max 75 characters
- [ ] Lists use proper <ul>/<ol> with 8px spacing
- [ ] Links underline on hover

## 7. Responsive Behavior
- [ ] Mobile: 16px padding, 14px body, full width buttons, hamburger menu
- [ ] Tablet: 24px padding, 16px body, inline buttons
- [ ] Desktop: 32px padding, 16px body, inline buttons, full nav items
- [ ] Modal: Full screen mobile, 90% tablet, max-width desktop

## 8. Accessibility
- [ ] All interactive elements keyboard focusable
- [ ] Focus indicators: 2px Primary ring, no outline removal
- [ ] Images have descriptive alt text
- [ ] Icons have aria-hidden="true" + text label
- [ ] Color is never only means of conveying information
- [ ] Headings follow proper hierarchy (h1 → h2 → h3)
- [ ] Forms use fieldset/legend where appropriate

## 9. Performance & Assets
- [ ] Icons: Single SVG sprite or consistent library (24x24px)
- [ ] Images: WebP, lazy-loaded, width/height attributes
- [ ] Fonts: Self-hosted or Google Fonts with display=swap
- [ ] No unnecessary external dependencies

## 10. Anti-Patterns (Strictly Forbidden)
- [ ] No more than 3 different font families
- [ ] No pure black (#000) for text
- [ ] No pure white (#FFF) on bright backgrounds without contrast check
- [ ] No overlapping elements without z-index management
- [ ] No fixed heights on text containers
- [ ] No autoplay videos/carousels
- [ ] No custom scrollbars that break native behavior

## 11. Dark Mode
- [ ] Surface and Text colors inverted
- [ ] Shadows adjusted for dark backgrounds
- [ ] All components render correctly in dark mode
