import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import 'notyf/notyf.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'

// Import our custom CSS
import './scss/styles.scss'


// Import all of Bootstrap's JS
import * as bootstrap from 'bootstrap'


const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')

window.bootstrap = bootstrap

// Use the address in env vars if specified
const apiEndpoint = import.meta.env.VITE_AIVOC_API_ENDPOINT
if (apiEndpoint !== undefined && apiEndpoint !== '') {
    window.API_ENDPOINT = apiEndpoint
} else {
    // Use current host as the API endpoint
    window.API_ENDPOINT = ''
}