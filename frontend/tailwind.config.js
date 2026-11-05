import frappeUIPreset, { content as frappeUIContent } from 'frappe-ui/tailwind'

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    ...frappeUIContent,
    // linked @whatsapp/ui source — its icons are `lucide-*` utility classes, and an
    // unscanned linked package fails silently: no error, every icon renders as blank space
    '../../whatsapp/ui/src/**/*.{vue,js,ts,jsx,tsx}',
    // linked @framework/ui source, for the Grid and Link the account form uses
    '../../frappe/ui/src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  safelist: [
    '!text-gray-700',
    '!text-blue-600',
    '!text-green-700',
    '!text-red-600',
    '!text-pink-600',
    '!text-orange-600',
    '!text-amber-600',
    '!text-yellow-600',
    '!text-cyan-600',
    '!text-teal-600',
    '!text-violet-600',
    '!text-purple-600',
    '!text-ink-gray-9',
  ],
  theme: {
    extend: {
      borderRadius: {
        none: '0px',
        sm: '2px',
        DEFAULT: '3px',
        md: '4px',
        lg: '4px',
        xl: '4px',
        '2xl': '4px',
        '3xl': '4px',
        '1': '2px',
        '2': '3px',
        '3': '3px',
        '4': '4px',
        '5': '4px',
        '6': '4px',
        '7': '4px',
        '8': '4px',
        '9': '4px',
        full: '9999px',
      },
    },
  },
  plugins: [],
}
