/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-cyan': '#06b6d4',
        'brand-blue': '#3b82f6',
      },
    },
  },
  plugins: [],
}
