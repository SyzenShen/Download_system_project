<template>
  <div class="page-center container">
    <div class="card page-card hero-card">
      <div class="card-header" style="text-align: center;">
        <h1 class="card-title title-stable text-white">欢迎使用文件管理系统</h1>
      </div>
      <div class="card-body">
        
        
        <div v-if="!isAuthenticated" style="margin-bottom: 30px;">
          <h3 class="text-white" style="margin-bottom: 15px;">开始使用</h3>
          <p class="lead">
            请先登录或注册账户以使用文件管理功能。
          </p>
          <div style="display: flex; gap: 12px; justify-content: center;">
            <router-link to="/login" class="btn btn-primary">立即登录</router-link>
            <router-link to="/register" class="btn btn-secondary">注册账户</router-link>
          </div>
        </div>
        
        <div v-else style="margin-bottom: 30px;">
          <h3 class="text-white" style="margin-bottom: 15px;">快速操作</h3>
          <div style="display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; margin-top: 24px;">
            <router-link to="/files" class="btn btn-primary">查看我的文件</router-link>
            <router-link to="/profile" class="btn btn-secondary">个人资料</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'Home',
  setup() {
    const authStore = useAuthStore()
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    
    return {
      isAuthenticated
    }
  }
}
</script>
<style scoped>
</style>
