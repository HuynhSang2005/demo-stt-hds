import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'transcript-neutral': 'var(--color-transcript-neutral)',
        'transcript-positive': 'var(--color-transcript-positive)',
        'transcript-negative': 'var(--color-transcript-negative)',
        'transcript-toxic': 'var(--color-transcript-toxic)',
      },
      animation: {
        'pulse-recording': 'pulse-recording 1s ease-in-out infinite',
        'waveform-pulse': 'waveform-pulse 0.8s ease-in-out infinite',
      },
    },
  },
  plugins: [],
} satisfies Config