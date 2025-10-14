<template>
  <div class="page-center">
    <div class="card page-card auth-wide">
      <div class="card-header">
        <h2 class="card-title title-stable text-white">用户登录</h2>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-error">
          {{ error }}
        </div>
        
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="username" class="form-label text-white">用户名</label>
            <input
              type="text"
              id="username"
              v-model="form.username"
              class="form-control"
              required
              :disabled="isLoading"
            />
          </div>
          
          <div class="form-group">
            <label for="password" class="form-label text-white">密码</label>
            <input
              type="password"
              id="password"
              v-model="form.password"
              class="form-control"
              required
              :disabled="isLoading"
            />
          </div>
          
          <div class="form-group submit-group">
            <button
              type="submit"
              class="btn btn-primary"
              style="width: 100%;"
              :disabled="isLoading"
            >
              <span v-if="isLoading" class="loading"></span>
              {{ isLoading ? '登录中...' : '登录' }}
            </button>
          </div>
        </form>
        
        <div style="text-align: center; margin-top: 12px;">
          <p class="text-friendly">
            还没有账户？
            <router-link to="/register">
              立即注册
            </router-link>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const form = ref({
      username: '',
      password: ''
    })
    
    const isLoading = computed(() => authStore.isLoading)
    const error = computed(() => authStore.error)
    
    const handleLogin = async () => {
      const result = await authStore.login(form.value)
      if (result.success) {
        router.push('/')
      }
    }
    
    return {
      form,
      isLoading,
      error,
      handleLogin
    }
  }
}
</script>

<style scoped>
/* 登录页输入框圆角 */
.page-card.auth-wide .form-control {
  border-radius: var(--radius-lg);
}
/* 整体上移输入区域：压缩标题与表单间距、减少组间距 */
.page-card.auth-wide .card-body {
  padding-top: 12px;
}
.page-card.auth-wide form {
  margin-top: 4px;
}
.page-card.auth-wide .form-group {
  margin-bottom: 12px;
}
/* 提交按钮组下移，匹配标题到用户名的视觉间距 */
.page-card.auth-wide .submit-group {
  margin-top: 16px;
}
</style>