<template>
  <div class="profile">
    <div class="card">
      <div class="card-header">
        <h2 class="card-title text-white">个人资料</h2>
      </div>
      <div class="card-body">
        <div v-if="currentUser">
          <div class="profile-info">
            <div class="info-item">
              <label class="info-label text-white">用户名:</label>
              <span class="info-value text-white">{{ currentUser.username }}</span>
            </div>
            
            <div class="info-item">
              <label class="info-label text-white">邮箱:</label>
              <span class="info-value text-white">{{ currentUser.email }}</span>
            </div>
            
            <div class="info-item">
              <label class="info-label text-white">注册时间:</label>
              <span class="info-value text-white">{{ formatDate(currentUser.date_joined) }}</span>
            </div>
            
            <div class="info-item">
              <label class="info-label text-white">最后登录:</label>
              <span class="info-value text-white">{{ formatDate(currentUser.last_login) }}</span>
            </div>
          </div>
          
          <div style="margin-top: 30px;">
            <h3 class="text-white" style="margin-bottom: 15px;">账户统计</h3>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-number">{{ fileCount }}</div>
                <div class="stat-label">上传文件数</div>
              </div>
              <div class="stat-item">
                <div class="stat-number">{{ formatFileSize(totalFileSize) }}</div>
                <div class="stat-label">总文件大小</div>
              </div>
            </div>
          </div>
          
          
        </div>
        
        <div v-else style="text-align: center; padding: 40px;">
          <div class="loading"></div>
          <p style="margin-top: 10px; color: #605e5c;">加载用户信息中...</p>
        </div>
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
</style>

<style scoped>
.profile-info {
  display: grid;
  gap: 15px;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: none;
}

.info-label {
  font-weight: 600;
  color: #ffffff;
  min-width: 100px;
  margin-right: 20px;
}

.info-value {
  color: #ffffff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  margin-top: 15px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background-color: #faf9f8;
  border-radius: 20px;
  /* 去掉左侧蓝色描边 */
  border-left: none;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: var(--brand-blue);
  margin-bottom: 5px;
}

.stat-label {
  color: #000000;
  font-size: 14px;
}
</style>