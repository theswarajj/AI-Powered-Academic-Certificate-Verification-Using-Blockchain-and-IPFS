/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Base — clean white canvas
        base: {
          DEFAULT: '#FFFFFF',
          elevated: '#F7F8FA',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          hover: '#F1F3F7',
          muted: '#F7F8FA',
        },
        border: {
          subtle: '#E5E7EB',
          strong: '#D1D5DB',
          accent: '#C7D2FE',
        },
        text: {
          primary: '#111827',
          secondary: '#6B7280',
          tertiary: '#9CA3AF',
        },
        // Brand — premium indigo-violet
        primary: {
          DEFAULT: '#6366F1',
          hover: '#4F46E5',
          light: '#EEF2FF',
          glow: 'rgba(99, 102, 241, 0.20)',
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
        },
        accent: {
          purple: '#8B5CF6',
          pink: '#EC4899',
          cyan: '#06B6D4',
          blue: '#3B82F6',
        },
        // Verdicts
        verdict: {
          verified: '#059669',
          investigation: '#D97706',
          revoked: '#DC2626',
          hash: '#DC2626',
          content: '#B91C1C',
          notfound: '#6B7280',
          partial: '#2563EB',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      borderRadius: {
        'card': '20px',
        'btn': '12px',
        'pill': '999px',
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.04)',
        'card-hover': '0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04)',
        'elevated': '0 8px 32px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03)',
        'primary': '0 4px 14px rgba(99, 102, 241, 0.30)',
        'primary-lg': '0 6px 24px rgba(99, 102, 241, 0.35)',
        'inner-glow': 'inset 0 1px 0 rgba(255,255,255,0.8)',
        'nav': '0 1px 3px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.03)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'scan-line': 'scan-line 2s linear infinite',
        'fade-in': 'fade-in 0.5s ease-out',
        'slide-up': 'slide-up 0.5s ease-out',
        'slide-in-right': 'slide-in-right 0.4s ease-out',
        'count-up': 'count-up 1s ease-out',
        'gauge-sweep': 'gauge-sweep 1.2s ease-in-out',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 8px rgba(99, 102, 241, 0.15)' },
          '50%': { boxShadow: '0 0 28px rgba(99, 102, 241, 0.30)' },
        },
        'scan-line': {
          '0%': { transform: 'translateY(0%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        'gauge-sweep': {
          '0%': { transform: 'rotate(-90deg)' },
          '100%': { transform: 'rotate(var(--gauge-angle))' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [],
}
