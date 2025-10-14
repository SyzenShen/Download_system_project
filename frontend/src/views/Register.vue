<template>
  <div class="page-center">
    <div class="card page-card narrow">
      <div class="card-header">
        <h2 class="card-title title-stable text-white">用户注册</h2>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-error">
          {{ error }}
        </div>
        
        <div v-if="successMessage" class="alert alert-success">
          {{ successMessage }}
        </div>
        
        <form @submit.prevent="handleRegister">
          <div class="form-group">
            <label for="username" class="form-label text-white">用户名</label>
            <input
              type="text"
              id="username"
              v-model="form.username"
              class="form-control"
              required
              :disabled="isLoading"
              minlength="3"
            />
            <small style="color: #605e5c;">用户名至少3个字符</small>
          </div>
          
          <div class="form-group">
            <label for="email" class="form-label text-white">邮箱</label>
            <input
              type="email"
              id="email"
              v-model="form.email"
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
              minlength="6"
            />
            <small style="color: #605e5c;">密码至少6个字符</small>
          </div>
          
          <div class="form-group">
            <label for="confirmPassword" class="form-label text-white">确认密码</label>
            <input
              type="password"
              id="confirmPassword"
              v-model="form.confirmPassword"
              class="form-control"
              required
              :disabled="isLoading"
            />
            <small v-if="form.password && form.confirmPassword && form.password !== form.confirmPassword" 
                   style="color: #d13438;">
              密码不匹配
            </small>
          </div>
          
          <div class="form-group">
            <button
              type="submit"
              class="btn btn-primary"
              style="width: 100%;"
              :disabled="isLoading || form.password !== form.confirmPassword"
            >
              <span v-if="isLoading" class="loading"></span>
              {{ isLoading ? '注册中...' : '注册' }}
            </button>
          </div>
        </form>
        
        <div style="text-align: center; margin-top: 12px;">
          <p class="text-friendly">
            已有账户？
            <router-link to="/login" style="text-decoration: none;">
              立即登录
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
  name: 'Register',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const form = ref({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
    
    const successMessage = ref('')
    
    const isLoading = computed(() => authStore.isLoading)
    const error = computed(() => authStore.error)
    
    const handleRegister = async () => {
      if (form.value.password !== form.value.confirmPassword) {
        return
      }
      
      const result = await authStore.register({
        username: form.value.username,
        email: form.value.email,
        password: form.value.password,
        // 后端序列化器要求字段名为 confirm_password
        confirm_password: form.value.confirmPassword
      })
      
      if (result.success) {
        successMessage.value = result.message
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      }
    }
    
    return {
      form,
      isLoading,
      error,
      successMessage,
      handleRegister
    }
  }
}
</script>

<style scoped>
/* 注册页输入框改为大圆角，并略增内边距以提升舒适度 */
.card.page-card.narrow .form-control {
  border-radius: var(--radius-lg) !important;
  padding: 12px 14px !important;
}
 </style>