<template>
  <div class="waves-corporate-bg">
    <div class="page-center container">
      <div class="card page-card hero-card waves-well">
        <div class="card-header" style="text-align: center;">
          <h1 class="card-title title-stable waves-text-corporate hero-title">BioFileManager</h1>
          <p class="waves-text-light hero-subtitle">Upload, organize and manage your files with ease</p>
        </div>
        <div class="card-body">
        
        
        <div v-if="!isAuthenticated" class="welcome-section">
          <h3 class="waves-text-corporate section-title">开始使用</h3>
          <div class="action-buttons">
            <router-link to="/login" class="btn btn-primary waves-btn">立即登录</router-link>
            <router-link to="/register" class="btn btn-secondary waves-btn">注册账户</router-link>
          </div>

        </div>
        
        <div v-else class="dashboard-section">
          <h3 class="waves-text-corporate section-title">欢迎回来，{{ currentUser?.username || '用户' }}！</h3>
          
          <div class="action-buttons">
            <router-link to="/files" class="btn btn-primary waves-btn">
              查看我的文件
            </router-link>
            <router-link to="/profile" class="btn btn-secondary waves-btn">
              个人资料
            </router-link>
          </div>
          

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
    const currentUser = computed(() => authStore.currentUser)
    
    return {
      isAuthenticated,
      currentUser
    }
  }
}

</script>
<style scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.hero-card {
  max-width: 800px;
  width: 100%;
  text-align: center;
  padding: 32px;
  border-radius: var(--radius-lg);
  background: #ffffff;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  margin: 2rem auto;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 12px;
  color: #1a1a1a;
  line-height: 1.2;
}

.hero-subtitle {
  font-size: 1.2rem;
  margin-bottom: 24px;
  color: #666666;
  font-weight: 400;
  line-height: 1.4;
}

.section-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--waves-text-corporate);
}

.welcome-section,
.dashboard-section {
  margin-bottom: 40px;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
  margin: 32px 0;
}

.waves-btn {
  padding: 6px 28px;
  border-radius: var(--waves-radius-sm);
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 140px;
  justify-content: center;
}

.btn-primary.waves-btn {
  background: #0078d4;
  color: #ffffff;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 120, 212, 0.3);
}

.btn-primary.waves-btn:hover {
  background: #106ebe;
  color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 120, 212, 0.4);
}

.btn-secondary.waves-btn {
  background: transparent;
  color: #0078d4;
  border: 2px solid #0078d4;
  box-shadow: 0 2px 4px rgba(0, 120, 212, 0.3);
}

.btn-secondary.waves-btn:hover {
  background: #0078d4;
  color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 120, 212, 0.4);
}

.btn-success.waves-btn {
  background: var(--waves-success);
  color: white;
  box-shadow: var(--waves-shadow-md);
}

.btn-success.waves-btn:hover {
  background: var(--waves-success-hover);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-lg);
}

.btn-icon {
  font-size: 1.1rem;
}

.features-preview {
  margin-top: 48px;
  padding-top: 32px;
  border-top: 1px solid var(--waves-border-color);
}

.features-preview h4 {
  font-size: 1.4rem;
  font-weight: 600;
  margin-bottom: 24px;
  color: var(--waves-text-corporate);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-top: 24px;
}

.feature-item {
  background: var(--waves-card-secondary-bg);
  padding: 24px;
  border-radius: var(--waves-border-radius);
  border: var(--waves-border-subtle);
  transition: all 0.3s ease;
}

.feature-item:hover {
  transform: translateY(-4px);
  box-shadow: var(--waves-shadow-lg);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 16px;
}

.feature-item h5 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--waves-text-corporate);
}

.feature-item p {
  font-size: 0.9rem;
  color: var(--waves-text-light);
  margin: 0;
  line-height: 1.5;
}



.lead {
  font-size: 1.1rem;
  margin-bottom: 24px;
  color: var(--waves-text-light);
  line-height: 1.6;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-card {
    padding: 32px 24px;
  }
  
  .hero-title {
    font-size: 2.2rem;
  }
  
  .hero-subtitle {
    font-size: 1.1rem;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
  
  .waves-btn {
    width: 100%;
    max-width: 280px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .home-container {
    padding: 16px;
  }
  
  .hero-card {
    padding: 24px 16px;
  }
  
  .hero-title {
    font-size: 1.8rem;
  }
}
</style>






