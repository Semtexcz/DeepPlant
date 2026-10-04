import { createApp } from 'vue'

import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
// Canonical utility layer first, then the genuinely global DeepPlant layer
// (semantic tokens, minimal reset, root sizing, typography) so the global layer
// wins where the two overlap.
import 'virtual:uno.css'
import './styles.css'
import App from './App.vue'

createApp(App).mount('#app')
