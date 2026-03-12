import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // ── Gruvbox background hierarchy ──────────────────────────────
        surface: {
          DEFAULT: '#282828',   // bg medium
          hard:    '#1d2021',   // bg hard (deepest)
          soft:    '#32302f',   // bg soft
          light:   '#3c3836',   // bg1
          lighter: '#504945',   // bg2
        },

        // ── Primary accent = Gruvbox yellow (warm, iconic) ────────────
        accent: {
          DEFAULT: '#d79921',   // yellow
          light:   '#fabd2f',   // yellow bright
          dim:     '#b57614',   // yellow dark
        },

        // ── Semantic UI states → Gruvbox equivalents ──────────────────
        success: '#b8bb26',    // green bright
        warn:    '#fe8019',    // orange bright
        danger:  '#fb4934',    // red bright
        info:    '#83a598',    // blue bright

        // ── Full named Gruvbox palette (for fine-grained use) ─────────
        gruvbox: {
          'fg':            '#ebdbb2',
          'fg1':           '#d5c4a1',
          'fg2':           '#bdae93',
          'fg3':           '#a89984',
          'fg4':           '#928374',
          'red':           '#cc241d',
          'red-bright':    '#fb4934',
          'green':         '#98971a',
          'green-bright':  '#b8bb26',
          'yellow':        '#d79921',
          'yellow-bright': '#fabd2f',
          'blue':          '#458588',
          'blue-bright':   '#83a598',
          'purple':        '#b16286',
          'purple-bright': '#d3869b',
          'aqua':          '#689d6a',
          'aqua-bright':   '#8ec07c',
          'orange':        '#d65d0e',
          'orange-bright': '#fe8019',
          'gray':          '#928374',
        },

        // ── Override Tailwind slate → Gruvbox fg/bg scale ────────────
        // All existing text-slate-* / border-slate-* classes now use
        // Gruvbox colours automatically — no component edits needed.
        slate: {
          50:  '#f9f5d7',
          100: '#f2e5bc',
          200: '#ebdbb2',   // fg
          300: '#d5c4a1',   // fg1
          400: '#bdae93',   // fg2
          500: '#a89984',   // fg3
          600: '#928374',   // gray
          700: '#7c6f64',   // bg4
          800: '#665c54',   // bg3
          900: '#504945',   // bg2
          950: '#3c3836',   // bg1
        },
      },

      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },

      animation: {
        'soft-pulse':    'soft-pulse 2s ease-in-out infinite',
        'warm-glow':     'warm-glow 3s ease-in-out infinite',
        'amber-flicker': 'amber-flicker 4s ease-in-out infinite',
      },

      keyframes: {
        'soft-pulse': {
          '0%, 100%': { opacity: '1'   },
          '50%':       { opacity: '0.4' },
        },
        'warm-glow': {
          '0%, 100%': { boxShadow: '0 0 8px rgba(215,153,33,0.2)'  },
          '50%':       { boxShadow: '0 0 22px rgba(250,189,47,0.45)' },
        },
        'amber-flicker': {
          '0%, 90%, 100%': { opacity: '1'    },
          '92%':            { opacity: '0.85' },
          '95%':            { opacity: '1'    },
          '97%':            { opacity: '0.9'  },
        },
      },
    },
  },
  plugins: [],
}

export default config
