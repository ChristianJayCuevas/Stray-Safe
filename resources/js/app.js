import '../css/app.css';
import '../css/global-theme.css'; // Import global theme CSS
import './bootstrap';

import { createInertiaApp } from '@inertiajs/vue3';
import { resolvePageComponent } from 'laravel-vite-plugin/inertia-helpers';
import { createApp, h } from 'vue';
import { ZiggyVue } from '../../vendor/tightenco/ziggy';

// Import Quasar and plugins
import { Quasar, Notify, Dialog } from 'quasar'; 
import '@quasar/extras/material-icons/material-icons.css';
import '@quasar/extras/fontawesome-v6/fontawesome-v6.css';

// Import additional libraries
import VueVideoPlayer from '@videojs-player/vue';
import 'video.js/dist/video-js.css';
import 'quasar/src/css/index.sass'; // Quasar core styles
import VueApexCharts from "vue3-apexcharts";

// Get app name from environment variables
const appName = "Stray Safe";

// Create the app
createInertiaApp({
    title: (title) => `${title} ${appName}`,
    resolve: (name) =>
        resolvePageComponent(
            `./Pages/${name}.vue`,
            import.meta.glob('./Pages/**/*.vue'),
        ),
    setup({ el, App, props, plugin }) {
        return createApp({ render: () => h(App, props) })
            .use(plugin)
            .use(ZiggyVue)
            .use(Quasar, {
                plugins: {
                    Notify,
                    Dialog, // Add Dialog plugin
                },
            })
            .use(VueVideoPlayer)
            .use(VueApexCharts)
            .mount(el);
    },
    progress: {
        color: '#4B5563',
    },
});
