<template>
  <div class="waves-corporate-bg">
    <div class="page-center">
      <div class="card page-card waves-auth-card waves-well">
        <div class="card-header waves-auth-header">
          <h2 class="card-title waves-text-corporate">用户注册</h2>
          <p class="waves-text-light">创建您的企业账户</p>
        </div>
        <div class="card-body waves-auth-body">
          <div v-if="error" class="alert alert-error waves-alert-error">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="currentColor"/>
            </svg>
            {{ error }}
          </div>
          
          <div v-if="successMessage" class="alert alert-success waves-alert-success">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
            </svg>
            {{ successMessage }}
          </div>
          
          <form @submit.prevent="handleRegister" class="waves-auth-form">
            <div class="form-group waves-form-group">
              <label for="username" class="form-label waves-form-label">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12ZM12 14C9.33 14 4 15.34 4 18V20H20V18C20 15.34 14.67 14 12 14Z" fill="currentColor"/>
                </svg>
                用户名
              </label>
              <input
                type="text"
                id="username"
                v-model="form.username"
                class="form-control waves-form-control"
                placeholder="请输入用户名（至少3个字符）"
                required
                :disabled="isLoading"
                minlength="3"
              />
              <small class="waves-form-hint">用户名至少3个字符</small>
            </div>
            
            <div class="form-group waves-form-group">
              <label for="email" class="form-label waves-form-label">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 4H4C2.9 4 2.01 4.9 2.01 6L2 18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6C22 4.9 21.1 4 20 4ZM20 8L12 13L4 8V6L12 11L20 6V8Z" fill="currentColor"/>
                </svg>
                邮箱地址
              </label>
              <input
                type="email"
                id="email"
                v-model="form.email"
                class="form-control waves-form-control"
                placeholder="请输入您的邮箱地址"
                required
                :disabled="isLoading"
              />
            </div>
            
            <div class="form-group waves-form-group">
              <label for="password" class="form-label waves-form-label">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 8H17V6C17 3.24 14.76 1 12 1S7 3.24 7 6V8H6C4.9 8 4 8.9 4 10V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V10C20 8.9 19.1 8 18 8ZM12 17C10.9 17 10 16.1 10 15S10.9 13 12 13 14 13.9 14 15 13.1 17 12 17ZM15.1 8H8.9V6C8.9 4.29 10.29 2.9 12 2.9S15.1 4.29 15.1 6V8Z" fill="currentColor"/>
                </svg>
                密码
              </label>
              <input
                type="password"
                id="password"
                v-model="form.password"
                class="form-control waves-form-control"
                placeholder="请输入密码（至少6个字符）"
                required
                :disabled="isLoading"
                minlength="6"
              />
              <small class="waves-form-hint">密码至少6个字符</small>
            </div>
            
            <div class="form-group waves-form-group">
              <label for="confirmPassword" class="form-label waves-form-label">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
                </svg>
                确认密码
              </label>
              <input
                type="password"
                id="confirmPassword"
                v-model="form.confirmPassword"
                class="form-control waves-form-control"
                :class="{ 'waves-form-error': form.password && form.confirmPassword && form.password !== form.confirmPassword }"
                placeholder="请再次输入密码"
                required
                :disabled="isLoading"
              />
              <small v-if="form.password && form.confirmPassword && form.password !== form.confirmPassword" 
                     class="waves-form-error-text">
                密码不匹配
              </small>
            </div>
            
            <div class="form-group waves-submit-group">
              <button
                type="submit"
                class="btn btn-primary waves-btn waves-btn-primary"
                :disabled="isLoading || form.password !== form.confirmPassword"
              >
                <span v-if="isLoading" class="waves-loading-spinner"></span>
                {{ isLoading ? '注册中...' : '立即注册' }}
              </button>
            </div>
          </form>
          
          <div class="waves-auth-footer">
            <div class="waves-divider">
              <span class="waves-divider-text">或</span>
            </div>
            <p class="waves-text-light">
              已有账户？
              <router-link to="/login" class="waves-link">
                立即登录
              </router-link>
            </p>
          </div>
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
/* 页面布局样式 */
.page-center {
  min-height: 100vh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 20px 20px;
}

/* 企业级认证卡片样式 */
.waves-auth-card {
  max-width: 520px;
  width: 100%;
  background: var(--waves-card-bg);
  backdrop-filter: var(--waves-backdrop-filter);
  border: var(--waves-border-subtle);
  border-radius: var(--waves-border-radius-xl);
  box-shadow: var(--waves-shadow-xl);
  overflow: hidden;
}
.waves-auth-card {
  transform: translateY(-40px); /* 轻微上移，视觉平衡 */
}

.waves-auth-header {
  text-align: center;
  padding: 48px 48px 32px;
  background: linear-gradient(135deg, var(--waves-primary-50) 0%, var(--waves-primary-100) 100%);
  border-bottom: var(--waves-border-subtle);
}



.waves-auth-header .card-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--waves-text-primary);
}

.waves-auth-header p {
  font-size: 1.1rem;
  margin: 0;
  opacity: 0.8;
}

.waves-auth-body {
  padding: 48px;
}

/* 错误和成功提示样式 */
.waves-alert-error {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: var(--waves-error-50);
  border: 1px solid var(--waves-error-200);
  border-radius: var(--waves-border-radius-lg);
  color: var(--waves-error-700);
  margin-bottom: 32px;
  font-weight: 500;
}

.waves-alert-error svg {
  flex-shrink: 0;
  color: var(--waves-error-500);
}

.waves-alert-success {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: var(--waves-success-50);
  border: 1px solid var(--waves-success-200);
  border-radius: var(--waves-border-radius-lg);
  color: var(--waves-success-700);
  margin-bottom: 32px;
  font-weight: 500;
}

.waves-alert-success svg {
  flex-shrink: 0;
  color: var(--waves-success-500);
}

/* 表单样式 */
.waves-auth-form {
  margin-bottom: 32px;
}

.waves-form-group {
  margin-bottom: 24px;
}

.waves-form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--waves-text-primary);
  margin-bottom: 8px;
  font-size: 0.95rem;
}

.waves-form-label svg {
  color: var(--waves-primary-500);
}

.waves-form-control {
  width: 100%;
  padding: 16px 20px;
  border: 2px solid #e5e7eb;
  border-radius: 4px;
  background: #ffffff;
  color: #1f2937;
  font-size: 1rem;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.waves-form-control::placeholder {
  color: #9ca3af;
}

.waves-form-control:focus {
  outline: none;
  border-color: #0078d4;
  box-shadow: 0 2px 4px rgba(0, 120, 212, 0.3);
  background: #ffffff;
}

.waves-form-control:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 表单错误状态 */
.waves-form-control.waves-form-error {
  border-color: var(--waves-error-500);
  background: var(--waves-error-50);
}

.waves-form-control.waves-form-error:focus {
  border-color: var(--waves-error-500);
  box-shadow: 0 0 0 3px var(--waves-error-100);
}

/* 表单提示文本 */
.waves-form-hint {
  display: block;
  margin-top: 6px;
  font-size: 0.85rem;
  color: var(--waves-text-muted);
}

.waves-form-error-text {
  display: block;
  margin-top: 6px;
  font-size: 0.85rem;
  color: var(--waves-error-600);
  font-weight: 500;
}

/* 提交按钮样式 */
.waves-submit-group {
  margin-top: 32px;
}

.waves-btn-primary {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 32px;
  background: #0078d4;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 120, 212, 0.3);
}

.waves-btn-primary:hover:not(:disabled) {
  background: #106ebe;
  box-shadow: 0 4px 8px rgba(0, 120, 212, 0.4);
}

.waves-btn-primary:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: var(--waves-shadow-sm);
}

.waves-btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 加载动画 */
.waves-loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: waves-spin 1s linear infinite;
}

@keyframes waves-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 页脚样式 */
.waves-auth-footer {
  text-align: center;
}

.waves-divider {
  position: relative;
  margin: 32px 0;
}

.waves-divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--waves-border-color);
}

.waves-divider-text {
  position: relative;
  background: var(--waves-card-bg);
  padding: 0 16px;
  color: var(--waves-text-muted);
  font-size: 0.9rem;
}

.waves-auth-footer p {
  margin: 0;
  font-size: 1rem;
}

.waves-link {
  color: var(--waves-primary-500);
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s ease;
}

.waves-link:hover {
  color: var(--waves-primary-600);
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 640px) {
  .waves-auth-card {
    margin: 20px;
    max-width: none;
  }
  
  .waves-auth-header,
  .waves-auth-body {
    padding: 32px 24px;
  }
  
  .waves-auth-header {
    padding-bottom: 24px;
  }
  
  .waves-auth-icon {
    width: 64px;
    height: 64px;
    margin-bottom: 20px;
  }
  
  .waves-auth-header .card-title {
    font-size: 1.75rem;
  }
  
  .waves-form-control {
    padding: 10px 16px;
  }
  
  .waves-btn-primary {
    padding: 10px 24px;
    font-size: 1rem;
  }
  
  .waves-form-group {
    margin-bottom: 20px;
  }
}
</style>