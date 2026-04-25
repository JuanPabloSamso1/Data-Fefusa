/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        teal: {
          500: "#00c2a8",
          600: "#1a9e8e",
        },
        navy: {
          900: "#0b0e1a",
          800: "#111827",
          700: "#172035",
          600: "#1e2d40",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
