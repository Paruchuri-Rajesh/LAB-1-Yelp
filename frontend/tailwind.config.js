/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        yelp: {
          red: "#d32323",
          darkred: "#af1c1c",
          blue: "#0073bb",
          light: "#f5f5f5",
        },
      },
    },
  },
  plugins: [],
};
