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
            boxShadow: {
                'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                'glow': '0 0 20px rgba(176, 196, 177, 0.3)',
                'card': '0 4px 20px -5px rgba(0, 0, 0, 0.08)',
            },
            keyframes: {
                slideDown: {
                    '0%': { transform: 'translateY(-100%)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                fadeIn: {
                    '0%': { opacity: '0', transform: 'translateY(10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                shimmer: {
                    '0%': { backgroundPosition: '-200% 0' },
                    '100%': { backgroundPosition: '200% 0' },
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-5px)' },
                },
                scroll: {
                    '0%': { transform: 'translateX(0)' },
                    '100%': { transform: 'translateX(-50%)' },
                },
            },
            animation: {
                slideDown: 'slideDown 0.3s ease-out',
                fadeIn: 'fadeIn 0.4s ease-out',
                shimmer: 'shimmer 2s linear infinite',
                float: 'float 3s ease-in-out infinite',
                scroll: 'scroll 30s linear infinite',
            },
            transitionDuration: {
                '400': '400ms',
            },
        },
    },
    plugins: [],
}
