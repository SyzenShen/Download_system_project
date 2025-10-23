import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'
// WAVES企业级样式导入
import './assets/css/core.css'
import './assets/css/main.css'
import './assets/css/forms.css'
import { useAuthStore } from './stores/auth'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// 初始化认证状态
const authStore = useAuthStore()
authStore.initializeAuth()

app.mount('#app')