/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "ui-sans-serif", "system-ui"],
        serif: ["Literata", "ui-serif", "Georgia"],
      },
      colors: {
        ink: "#1b1b1b",
        muted: "#5a5a5a",
        accent: "#d84a1b",
        mint: "#b7e4c7",
        mist: "#eef2f6",
        sand: "#f7f1e6",
      },
      boxShadow: {
        soft: "0 18px 40px rgba(19, 19, 19, 0.08)",
        bold: "0 24px 60px rgba(19, 19, 19, 0.14)",
      },
      borderRadius: {
        xl: "20px",
        "2xl": "28px",
      },
      keyframes: {
        floatIn: {
          "0%": { transform: "translateY(14px)", opacity: 0 },
          "100%": { transform: "translateY(0)", opacity: 1 },
        },
      },
      animation: {
        floatIn: "floatIn 0.6s ease forwards",
      },
    },
  },
  plugins: [],
};
