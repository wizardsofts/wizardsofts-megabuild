/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Custom colors for trading signals
      colors: {
        buy: {
          light: "#dcfce7", // green-100
          DEFAULT: "#22c55e", // green-500
          dark: "#15803d", // green-700
        },
        sell: {
          light: "#fee2e2", // red-100
          DEFAULT: "#ef4444", // red-500
          dark: "#b91c1c", // red-700
        },
        hold: {
          light: "#fef3c7", // amber-100
          DEFAULT: "#f59e0b", // amber-500
          dark: "#b45309", // amber-700
        },
      },
    },
  },
  plugins: [],
};
