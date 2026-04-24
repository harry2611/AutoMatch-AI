import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#F7F3EB",
        ink: "#13212C",
        brand: {
          50: "#F6F7F2",
          100: "#E8E9D8",
          300: "#C9D09B",
          500: "#8DA35A",
          700: "#4C6431",
          900: "#203120"
        },
        accent: {
          500: "#E67E22",
          700: "#B7540A"
        },
        ocean: {
          500: "#0F8B8D",
          700: "#0B5D68"
        }
      },
      boxShadow: {
        panel: "0 20px 45px rgba(19, 33, 44, 0.12)"
      },
      backgroundImage: {
        "hero-grid":
          "radial-gradient(circle at top left, rgba(141,163,90,0.25), transparent 40%), radial-gradient(circle at bottom right, rgba(230,126,34,0.15), transparent 30%)"
      }
    }
  },
  plugins: [],
};

export default config;
