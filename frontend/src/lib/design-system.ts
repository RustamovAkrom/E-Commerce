/**
 * Design System — color tokens, spacing, radii, shadows, animation durations.
 *
 * Bu fayl barcha komponentlar va sahifalar uchun yagona manba hisoblanadi.
 * Dizayn o'zgarishlarini shu yerdan boshlang.
 */

// ─── Color Tokens ───────────────────────────────────────────────────────────

/**
 * HSL format: "hue saturation lightness"
 * Matched with CSS variables in globals.css via @theme inline.
 */
export const colors = {
  // Brand colors
  primary: {
    light: "222.2 47.4% 11.2%",   // hsl var: --primary
    dark: "210 40% 98%",           // hsl var: --primary-foreground
  },
  secondary: {
    light: "210 40% 96.1%",        // hsl var: --secondary
    dark: "217.2 32.6% 17.5%",     // hsl var: --secondary-foreground
  },
  accent: {
    light: "210 40% 96.1%",        // hsl var: --accent
    dark: "210 40% 98%",           // hsl var: --accent-foreground
  },
  surface: {
    light: "0 0% 100%",            // hsl var: --background
    dark: "222.2 84% 4.9%",        // hsl var: --background
  },
  muted: {
    foreground: "215.4 16.3% 46.9%",
    dark: "215 20.2% 65.1%",
  },
  border: {
    light: "214.3 31.8% 91.4%",
    dark: "217.2 32.6% 17.5%",
  },
  destructive: {
    light: "0 84.2% 60.2%",
    dark: "0 62.8% 30.6%",
  },
  ring: {
    light: "222.2 84% 4.9%",
    dark: "212.7 26.8% 83.9%",
  },
} as const;

// ─── Spacing Scale ──────────────────────────────────────────────────────────

/**
 * Multiplier for Tailwind spacing (1 unit = 0.25rem / 4px).
 * Usage: `p-${scale}` → Tailwind classes like p-2, p-4, etc.
 */
export const spacing = {
  xs:  "0.25rem",   // 4px
  sm:  "0.5rem",    // 8px
  md:  "1rem",      // 16px
  lg:  "1.5rem",    // 24px
  xl:  "2rem",      // 32px
  "2xl": "2.5rem",  // 40px
} as const;

// ─── Border Radius ──────────────────────────────────────────────────────────

export const borderRadius = {
  sm:  "0.375rem",   // 6px  (Tailwind: rounded-sm)
  md:  "0.5rem",     // 8px  (Tailwind: rounded-md)
  lg:  "0.75rem",    // 12px (Tailwind: rounded-lg)
  full:"9999px",     // pill (Tailwind: rounded-full)
} as const;

// ─── Shadow Scale ───────────────────────────────────────────────────────────

/**
 * CSS box-shadow values in px.
 * Tailwind class mapping: shadow-sm/md/lg/xl.
 */
export const shadows = {
  sm:  "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  md:  "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
  lg:  "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
  xl:  "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
} as const;

// ─── Animation Durations ────────────────────────────────────────────────────

export const animations = {
  fast:  "150ms",   // Button press, dropdown open
  normal:"300ms",   // Fade transitions, toast
  slow:  "500ms",   // Page transitions
} as const;

// ─── Breakpoints ────────────────────────────────────────────────────────────

/**
 * Tailwind default breakpoints in px.
 */
export const breakpoints = {
  sm:  "640px",   // Mobile landscape
  md:  "768px",   // Tablet
  lg:  "1024px",  // Laptop
  xl:  "1280px",  // Desktop
  "2xl": "1536px", // Large desktop
} as const;

// ─── Z-Index Scale ──────────────────────────────────────────────────────────

export const zIndex = {
  dropdown: 100,
  sticky: 200,
  overlay: 300,
  modal: 400,
  popover: 500,
  skipLink: 600,
  toast: 700,
} as const;

// ─── Container Max Widths ───────────────────────────────────────────────────

export const containers = {
  sm:  "640px",
  md:  "768px",
  lg:  "1024px",
  xl:  "1280px",
  "2xl": "1400px",
} as const;
