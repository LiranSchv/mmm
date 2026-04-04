import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#6366f1", light: "#a5b4fc", dark: "#4338ca" },
      },
    },
  },
  plugins: [],
};

export default config;
