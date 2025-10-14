<template>
  <nav class="navbar header">
    <div class="container" style="display: flex; justify-content: space-between; align-items: center;">
      <router-link to="/" class="navbar-brand">文件管理系统</router-link>
      
      <ul class="navbar-nav" style="display: flex; align-items: center;">
        <li class="nav-item" v-if="!isAuthenticated">
          <router-link to="/login" class="nav-link">登录</router-link>
        </li>
        <li class="nav-item" v-if="!isAuthenticated">
          <router-link to="/register" class="nav-link">注册</router-link>
        </li>
        
        <template v-if="isAuthenticated">
          <li class="nav-item">
            <router-link to="/files" class="nav-link">我的文件</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/upload" class="nav-link">上传文件</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/profile" class="nav-link">个人资料</router-link>
          </li>
          <li class="nav-item">
            <span class="nav-link nav-static">
              欢迎, {{ currentUser?.username || '用户' }}
            </span>
          </li>
          <li class="nav-item">
            <button @click="handleLogout" class="nav-link btn-gray-text" style="margin-left: 10px;">
              退出登录
            </button>
          </li>
</template>
      </ul>
    </div>
  </nav>
</template>

<script>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'Navbar',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    const currentUser = computed(() => authStore.currentUser)
    
    const handleLogout = async () => {
      await authStore.logout()
      router.push('/')
    }
    
    return {
      isAuthenticated,
      currentUser,
      handleLogout
    }
  }
}
</script>

<style scoped>
/* 灰色文字按钮用于退出登录，保持与导航文字一致大小 */
.btn-gray-text {
  background: transparent !important;
  color: #CCCCCC !important; /* 浅灰 */
  border: none !important;
  box-shadow: none !important;
  font: inherit;
  font-size: inherit;
}
.btn-gray-text:hover {
  color: #B3B3B3 !important; /* 悬停稍深灰，保证可见性 */
  text-decoration: none;
}

/* 欢迎文本为浅灰，悬停保持不变，与登录/退出一致 */
.nav-link.nav-static,
.nav-link.nav-static:hover {
  color: #CCCCCC !important;
  text-decoration: none;
  cursor: default;
}
</style>