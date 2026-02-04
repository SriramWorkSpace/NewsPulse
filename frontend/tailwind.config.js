/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,jsx}'],
    theme: {
        extend: {
            colors: {
                // Sophisticated Minimalist Palette
                warmBeige: '#FAF9F6',
                taupe: '#F5F0EC',
                charcoal: '#262626',
                mutedBrown: '#524A4A',
                sageGreen: '#B0C4B1',
                mutedRose: '#A26769',
                // Legacy colors
                cream: '#F7E8D3',
                mocha: '#A47864',
                slate: '#30364F',
            },
            backdropBlur: {
                xs: '2px',
            },
        },
    },
    plugins: [],
}
