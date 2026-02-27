/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Blueprint palette
        canvas: {
          900: '#0a0f1a',
          800: '#0f1729',
          700: '#141e35',
          600: '#1a2744',
        },
        blueprint: {
          cyan: '#00d4ff',
          teal: '#0ea5a0',
          accent: '#22d3ee',
          muted: '#3b5a7a',
          grid: '#1e3a5f',
        },
        text: {
          primary: '#e2e8f0',
          secondary: '#94a3b8',
          muted: '#64748b',
        }
      },
      fontFamily: {
        display: ['Playfair Display', 'Georgia', 'serif'],
        body: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'grid-pattern': `
          linear-gradient(to right, rgba(30, 58, 95, 0.3) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(30, 58, 95, 0.3) 1px, transparent 1px)
        `,
        'grid-fine': `
          linear-gradient(to right, rgba(30, 58, 95, 0.15) 1px, transparent 1px),
          linear-gradient(to bottom, rgba(30, 58, 95, 0.15) 1px, transparent 1px)
        `,
      },
      backgroundSize: {
        'grid': '40px 40px',
        'grid-fine': '10px 10px',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
        'draw-line': 'drawLine 1s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        drawLine: {
          '0%': { strokeDashoffset: '100%' },
          '100%': { strokeDashoffset: '0' },
        },
      },
    },
  },
  plugins: [],
}
