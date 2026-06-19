const mix = require('laravel-mix');
const path = require('path');

const domain = 'ateam.test'; // <== edit this one
const homedir = require('os').homedir();
/*
 |--------------------------------------------------------------------------
 | Mix Asset Management
 |--------------------------------------------------------------------------
 |
 | Mix provides a clean, fluent API for defining some Webpack build steps
 | for your Laravel applications. By default, we are compiling the CSS
 | file for the application as well as bundling up all the JS files.
 |
 */

mix.js('resources/js/app.js', 'public/js').postCss('resources/css/app.css', 'public/css', [
    require('postcss-import'),
    require('tailwindcss'),
    require('autoprefixer'),
])
.vue({ version: 3 })
.sass('resources/sass/style.scss', 'public/css')
.browserSync({
    proxy: 'https://' + domain,
    host: domain,
    open: 'external',
    https: { key: homedir + '/.config/valet/Certificates/' + domain + '.key', cert: homedir + '/.config/valet/Certificates/' + domain + '.crt', },
}).webpackConfig((webpack) => {
    return {
        plugins: [
            new webpack.DefinePlugin({
                __VUE_OPTIONS_API__: true,
                __VUE_PROD_DEVTOOLS__: false,
            }),
        ],
        resolve: {
            alias: {
              '@': path.resolve(__dirname, 'resources/js')
            },
          },
    };
});
