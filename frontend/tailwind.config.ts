import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f0f7f2",
          100: "#d4e9dc",
          200: "#a9d3b9",
          300: "#7ebc96",
          400: "#5E8A68",
          500: "#4d7857",
          600: "#3E6B4A",
          700: "#2E4A35",
          800: "#1f3224",
          900: "#0f1912",
        },
        warm: {
          50:  "#fef6ef",
          100: "#fde8d4",
          200: "#fad0a9",
          300: "#f7b87e",
          400: "#D6854A",
          500: "#C05A2B",
          600: "#9a4520",
          700: "#7a3518",
        },
        cream: "#FAF5ED",
        earth: "#1E1208",
        bark:  "#3B2010",
        gold:  "#C9A96E",
      },
      fontFamily: {
        sans:    ["Jost", "system-ui", "sans-serif"],
        display: ["Cormorant Garamond", "Georgia", "serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-gentle": "pulseGentle 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(16px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        pulseGentle: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.6" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
