/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f1720",
        sand: "#f4efe6",
        brass: "#b08d57",
        sea: "#1f4e5f",
      },
    },
  },
  plugins: [],
};
