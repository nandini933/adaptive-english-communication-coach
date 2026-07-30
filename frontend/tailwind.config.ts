import type { Config } from "tailwindcss";
export default { content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx}"
], theme:{extend:{colors:{ink:"#12263A",teal:"#0D9488",mist:"#F4F7FA"}}}, plugins:[] } satisfies Config;
