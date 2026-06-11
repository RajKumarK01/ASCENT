import type { Config } from 'tailwindcss'

export default {
  theme: {
    extend: {
      colors: {
        // GitHub dark theme
        github: {
          // Background colors
          bg: '#0d1117',        // Main background
          surface: '#161b22',   // Cards, panels
          border: '#30363d',    // Borders
          
          // Text colors
          text: '#c9d1d9',      // Primary text
          muted: '#8b949e',     // Muted/secondary text
          
          // Accent colors
          blue: '#58a6ff',      // Primary accent
          green: '#3fb950',     // Contribution: 1 task
          greenMed: '#26a641',  // Contribution: 2 tasks
          greenDark: '#1a7f37', // Contribution: 3+ tasks
          red: '#f85149',       // Error/negative
          yellow: '#d29922',    // Warning
          purple: '#bc8ef7',    // Secondary accent
        },
      },
      backgroundColor: {
        dark: '#0d1117',
        'dark-surface': '#161b22',
      },
      textColor: {
        dark: '#c9d1d9',
        'dark-muted': '#8b949e',
      },
      borderColor: {
        dark: '#30363d',
      },
    },
  },
  plugins: [],
} satisfies Config
