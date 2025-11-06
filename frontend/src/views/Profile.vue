<template>
  <div class="ms-profile-container">
    <div class="ms-profile-content">
      <!-- 简洁头部 -->
      <div class="ms-profile-header">
        <div class="ms-avatar">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 12C14.7614 12 17 9.76142 17 7C17 4.23858 14.7614 2 12 2C9.23858 2 7 4.23858 7 7C7 9.76142 9.23858 12 12 12Z"/>
            <path d="M12 14C7.58172 14 4 17.5817 4 22H20C20 17.5817 16.4183 14 12 14Z"/>
          </svg>
        </div>
        <h1 class="ms-title">个人资料</h1>
      </div>

      <div v-if="currentUser" class="ms-profile-body">
        <!-- 基本信息 -->
        <div class="ms-section">
          <h2 class="ms-section-title">基本信息</h2>
          <div class="ms-info-list">
            <div class="ms-info-row">
              <span class="ms-label">用户名</span>
              <span class="ms-value">{{ currentUser.username }}</span>
            </div>
            <div class="ms-info-row">
              <span class="ms-label">邮箱地址</span>
              <span class="ms-value">{{ currentUser.email }}</span>
            </div>
            <div class="ms-info-row">
              <span class="ms-label">注册时间</span>
              <span class="ms-value">{{ formatDate(currentUser.date_joined) }}</span>
            </div>
            <div class="ms-info-row">
              <span class="ms-label">最后登录</span>
              <span class="ms-value">{{ formatDate(currentUser.last_login) }}</span>
            </div>
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="ms-section">
          <h2 class="ms-section-title">账户统计</h2>
          <div class="ms-stats-grid">
            <div class="ms-stat-item">
              <div class="ms-stat-number">{{ fileCount }}</div>
              <div class="ms-stat-label">上传文件数</div>
            </div>
            <div class="ms-stat-item">
              <div class="ms-stat-number">{{ formatFileSize(totalFileSize) }}</div>
              <div class="ms-stat-label">总文件大小</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 加载状态 -->
      <div v-else class="ms-loading">
        <div class="ms-spinner"></div>
        <p>加载用户信息中...</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useFilesStore } from '../stores/files'

export default {
  name: 'Profile',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const filesStore = useFilesStore()
    
    const currentUser = computed(() => authStore.currentUser)
    const fileCount = computed(() => filesStore.files.length)
    const totalFileSize = computed(() => {
      // 使用后端返回的 file_size 字段进行累加，修复显示错误
      return filesStore.files.reduce((total, file) => total + (file.file_size || 0), 0)
    })
    
    const formatDate = (dateString) => {
      if (!dateString) return '未知'
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    const handleLogout = async () => {
      await authStore.logout()
      router.push('/')
    }
    
    onMounted(() => {
      // 获取用户文件统计信息
      filesStore.fetchFiles()
    })
    
    return {
      currentUser,
      fileCount,
      totalFileSize,
      formatDate,
      formatFileSize,
      handleLogout
    }
  }
}
</script>

<style scoped>
/* 微软风格个人资料页面 */
.ms-profile-container {
  min-height: 100vh;
  background: white;
  padding: 20px;
}

.ms-profile-content {
  max-width: 800px;
  margin: 0 auto;
}

/* 头部样式 */
.ms-profile-header {
  background: white;
  padding: 24px 32px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  --profile-primary: rgb(58, 126, 185);
  --profile-primary-hover: rgb(45, 102, 150);
}

.ms-avatar {
  width: 48px;
  height: 48px;
  background: var(--profile-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.ms-avatar svg {
  width: 24px;
  height: 24px;
}

.ms-title {
  font-size: 24px;
  font-weight: 600;
  color: #323130;
  margin: 0;
  line-height: 1.2;
}

/* 主体内容 */
.ms-profile-body {
  padding: 0;
}

.ms-section {
  padding: 24px 32px;
}

.ms-section-title {
  font-size: 18px;
  font-weight: 600;
  color: #323130;
  margin: 0 0 16px 0;
  line-height: 1.3;
}

/* 信息列表 */
.ms-info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ms-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  min-height: 32px;
}

.ms-label {
  font-size: 14px;
  font-weight: 500;
  color: #605e5c;
  flex-shrink: 0;
  width: 120px;
}

.ms-value {
  font-size: 14px;
  color: #323130;
  text-align: right;
  word-break: break-all;
  flex: 1;
}

/* 统计网格 */
.ms-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.ms-stat-item {
  background: #faf9f8;
  border-radius: var(--waves-radius-sm);
  padding: 16px;
  text-align: center;
  border-top: 2px solid var(--profile-primary);
}

.ms-stat-number {
  font-size: 28px;
  font-weight: 600;
  color: var(--profile-primary);
  margin-bottom: 4px;
  line-height: 1.2;
}

.ms-stat-label {
  font-size: 12px;
  color: #605e5c;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 加载状态 */
.ms-loading {
  text-align: center;
  padding: 48px 32px;
}

.ms-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #edebe9;
  border-top: 2px solid var(--profile-primary);
  border-radius: 50%;
  animation: ms-spin 1s linear infinite;
  margin: 0 auto 16px;
}

.ms-loading p {
  font-size: 14px;
  color: #605e5c;
  margin: 0;
}

@keyframes ms-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .ms-profile-container {
    padding: 16px;
  }
  
  .ms-profile-header {
    padding: 20px 24px 12px;
  }
  
  .ms-section {
    padding: 20px 24px;
  }
  
  .ms-title {
    font-size: 20px;
  }
  
  .ms-info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .ms-label {
    width: auto;
  }
  
  .ms-value {
    text-align: left;
  }
  
  .ms-stats-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .ms-profile-container {
    padding: 12px;
  }
  
  .ms-profile-header {
    padding: 16px 20px 8px;
    gap: 12px;
  }
  
  .ms-avatar {
    width: 40px;
    height: 40px;
  }
  
  .ms-avatar svg {
    width: 20px;
    height: 20px;
  }
  
  .ms-title {
    font-size: 18px;
  }
  
  .ms-section {
    padding: 16px 20px;
  }
  
  .ms-section-title {
    font-size: 16px;
  }
  
  .ms-stat-item {
    padding: 12px;
  }
  
  .ms-stat-number {
    font-size: 24px;
  }
}
</style>
