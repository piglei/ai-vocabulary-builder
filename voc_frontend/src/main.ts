import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// Import our custom CSS
import './scss/styles.scss'

// Import all of Bootstrap's JS
import * as bootstrap from 'bootstrap'


const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')

window.bootstrap = bootstrap
window.API_ENDPOINT = import.meta.env.VITE_API_ENDPOINT