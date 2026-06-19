const defaultTheme = require('tailwindcss/defaultTheme');

module.exports = {
    purge: [
        './vendor/laravel/framework/src/Illuminate/Pagination/resources/views/*.blade.php',
        './storage/framework/views/*.php',
        './resources/views/**/*.blade.php',
    ],

    theme: {
     
        extend: {
           
            fontFamily: {
                sans: ['Work Sans', ...defaultTheme.fontFamily.sans],
                heading: ["Work Sans", "serif"],
                body: ["Calibri", "cantarell", "sans-serif"]
                
            },
            spacing:{
                '15': '3.75rem',
                '23': '5.75rem',
                '100': '25rem',
                '128':'32rem',
                '144': '36rem',
            },
            colors:{
                'ateam-red': '#d8494f',
                'ateam-blue': '#1269a3',
                'ateam-blue-100': '#E8F6FF',
                'ateam-dark-blue':'#224760',
                'ateam-black': '#2d2d2d',
                'ateam-gray': '#7b7b7b'
            },
            fontSize:{
                'ateam-2xl': '9rem',
                'ateam-xl': '8rem',
                'ateam-action-xl' : '10rem',
                'ateam-action-2xl' : '12rem',
                'body-2xl': '1.4rem'
            },
            lineHeight:{
                'ateam-action-xl': '9rem',
                'ateam-action-2xl': '11rem',
                'ateam-2xl': '8rem',
                'ateam-xl': '7rem'
            },
        },
    },

    variants: {
       
        extend: {
            opacity: ['disabled'],
        },
    },

    plugins: [
        require('@tailwindcss/forms'),
        require("@tailwindcss/typography"),
        function({ addComponents, theme }) {
            addComponents({
                ".container": {
                    marginInline: "auto",
                    paddingInline: theme("spacing.4"),
                    maxWidth: theme("screens.sm"),

                    // Breakpoints
                    "@screen sm": {
                        maxWidth: theme("screens.sm")
                    },
                    "@screen md": {
                        maxWidth: theme("screens.md")
                    },
                    "@screen lg": {
                        maxWidth: "968px"
                    },
                    "@screen xl": {
                        maxWidth: "1200px"
                    },
                    "@screen 2xl": {
                        maxWidth: "1400px"
                    }
                }
            });
        }
    
    ],
};
