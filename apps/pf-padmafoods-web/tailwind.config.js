/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'padma-red': '#D12027',
        'padma-blue': '#3D72A4',
        'padma-dark': '#333333',
      },
      fontFamily: {
        'script': ['Great Vibes', 'Dancing Script', 'Parisienne', 'cursive'],
        'sans': ['Montserrat', 'Lato', 'Open Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
