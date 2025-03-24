import axios from 'axios';
window.axios = axios;

window.axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';

// Add CSRF token to all requests
const token = document.querySelector('meta[name="csrf-token"]');
if (token) {
    window.axios.defaults.headers.common['X-CSRF-TOKEN'] = token.getAttribute('content');
    window.axios.defaults.withCredentials = true;
}

// Set API token for API routes
window.axios.defaults.headers.common['Authorization'] = 'Bearer StraySafeTeam3';
