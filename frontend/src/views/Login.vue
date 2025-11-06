<template>
  <div class="waves-corporate-bg">
    <div class="page-center">
      <div class="card page-card waves-auth-card waves-well">
        <div class="card-header waves-auth-header">
          <h2 class="card-title waves-text-corporate">用户登录</h2>
          <p class="waves-text-light">登录您的企业账户</p>
        </div>
        <div class="card-body waves-auth-body">
          <div v-if="error" class="alert alert-error waves-alert-error">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C6.48 2 2 6.48 2 12S6.48 22 12 22 22 17.52 22 12 17.52 2 12 2ZM13 17H11V15H13V17ZM13 13H11V7H13V13Z" fill="currentColor"/>
            </svg>
            {{ error }}
          </div>
          
          <form @submit.prevent="handleLogin" class="waves-auth-form">
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
                placeholder="请输入您的密码"
                required
                :disabled="isLoading"
              />
            </div>
            
            <div class="form-group waves-submit-group">
              <button
                type="submit"
                class="btn btn-primary waves-btn waves-btn-primary"
                :disabled="isLoading"
              >
                <span v-if="isLoading" class="waves-loading-spinner"></span>
                {{ isLoading ? '登录中...' : '立即登录' }}
              </button>
            </div>
          </form>
          
          <div class="waves-auth-footer">
            <div class="waves-divider">
              <span class="waves-divider-text">或</span>
            </div>
            <p class="waves-text-light">
              还没有账户？
              <router-link to="/register" class="waves-link">
                立即注册
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
  name: 'Login',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const form = ref({
      email: '',
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
/* 页面布局样式 */
.page-center {
  min-height: 10vh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 20px 20px;
}

/* 企业级认证卡片样式 */
.waves-auth-card {
  max-width: 480px;
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

/* 错误提示样式 */
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

.waves-corporate-bg {
  --auth-primary: rgb(58, 126, 185);
  --auth-primary-hover: rgb(45, 102, 150);
  --auth-shadow: 0 2px 4px rgba(58, 126, 185, 0.3);
  --auth-shadow-hover: 0 4px 8px rgba(58, 126, 185, 0.4);
}

.waves-form-label svg {
  color: var(--auth-primary);
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
  border-color: var(--auth-primary);
  box-shadow: var(--auth-shadow);
  background: #ffffff;
}

.waves-form-control:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  background: var(--auth-primary) !important;
  color: white;
  border: none !important;
  border-radius: 4px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--auth-shadow);
}

.waves-btn-primary:hover:not(:disabled) {
  background: var(--auth-primary-hover) !important;
  box-shadow: var(--auth-shadow-hover);
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
  color: var(--auth-primary) !important;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s ease;
}

.waves-link:hover {
  color: var(--auth-primary-hover) !important;
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
    padding: 14px 16px;
  }
  
  .waves-btn-primary {
    padding: 10px 24px;
    font-size: 1rem;
  }
}
</style>
