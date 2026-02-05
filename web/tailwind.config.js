/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Sora', 'system-ui', 'sans-serif'],
      },
      colors: {
        bg: '#FAFAF8',
        surface: '#FFFFFF',
        text: '#1A1A18',
        muted: '#78756F',
        border: '#E8E6E1',
        accent: {
          DEFAULT: '#C53030',
          hover: '#A52828',
          light: '#FEF2F2',
        },
        success: {
          DEFAULT: '#2D8A7B',
          light: '#ECFDF5',
        },
        warning: {
          DEFAULT: '#D4880F',
          light: '#FFFBEB',
        },
        // Legacy primary for gradual migration
        primary: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          400: '#E57373',
          500: '#C53030',
          600: '#C53030',
          700: '#A52828',
        }
      },
      boxShadow: {
        'soft': '0 2px 8px -2px rgba(0, 0, 0, 0.08)',
        'medium': '0 4px 16px -4px rgba(0, 0, 0, 0.1)',
        'lift': '0 8px 24px -8px rgba(0, 0, 0, 0.12)',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
      }
    },
  },
  plugins: [],
}
