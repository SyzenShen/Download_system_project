<template>
  <div class="waves-file-manager">
    <!-- 顶部导航栏 -->
    <NavigationBar />
    
    <!-- 主内容区域 -->
    <div class="waves-main-content">
      <!-- 左侧目录树 -->
      <div class="waves-sidebar">
        <FolderTree />
      </div>
      
      <!-- 右侧文件显示区域 -->
      <div class="waves-content-area">
        <!-- 加载状态 -->
        <div v-if="isLoading" class="waves-loading-container">
          <div class="waves-loading-content">
            <div class="waves-loading-spinner">
              <svg class="waves-spinner-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2V6M12 18V22M4.93 4.93L7.76 7.76M16.24 16.24L19.07 19.07M2 12H6M18 12H22M4.93 19.07L7.76 16.24M16.24 7.76L19.07 4.93" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="waves-loading-text">正在加载文件...</div>
            <div class="waves-loading-description">请稍候，我们正在获取您的文件列表</div>
          </div>
        </div>
        
        <!-- 错误状态 -->
        <div v-else-if="error" class="waves-error-container">
          <div class="waves-error-content">
            <div class="waves-error-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="waves-error-title">加载失败</div>
            <div class="waves-error-message">{{ error }}</div>
            <div class="waves-error-actions">
              <button @click="refreshFiles" class="waves-btn waves-btn-primary">
                <svg class="waves-btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 4V10H7M23 20V14H17M20.49 9C19.9828 7.56678 19.1209 6.28392 17.9845 5.27493C16.8482 4.26595 15.4745 3.56905 13.9917 3.24575C12.5089 2.92246 10.9652 2.98546 9.51691 3.42597C8.06861 3.86649 6.76071 4.66872 5.71 5.75L1 10M23 14L18.29 18.25C17.2393 19.3313 15.9314 20.1335 14.4831 20.574C13.0348 21.0145 11.4911 21.0775 10.0083 20.7542C8.52547 20.431 7.1518 19.7341 6.01547 18.7251C4.87913 17.7161 4.01717 16.4332 3.51 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                重新加载
              </button>
              <button @click="goHome" class="waves-btn waves-btn-secondary">
                <svg class="waves-btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3 9L12 2L21 9V20C21 20.5304 20.7893 21.0391 20.4142 21.4142C20.0391 21.7893 19.5304 22 19 22H5C4.46957 22 3.96086 21.7893 3.58579 21.4142C3.21071 21.0391 3 20.5304 3 20V9Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M9 22V12H15V22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                返回首页
              </button>
            </div>
          </div>
        </div>
        
        <!-- 文件显示 -->
        <div v-else class="waves-file-display-container">
          <FileDisplay />
        </div>
      </div>
    </div>
     
    <!-- 上传文件对话框 -->
    <div v-if="showUploadDialog" class="waves-modal-overlay" @click="closeUploadDialog">
      <div class="waves-modal-container" @click.stop>
        <UploadDialog @close="closeUploadDialog" />
      </div>
    </div>
     
    <!-- 新建文件夹对话框 -->
    <div v-if="showNewFolderDialog" class="waves-modal-overlay" @click="closeNewFolderDialog">
      <div class="waves-modal-container" @click.stop>
        <NewFolderDialog @close="closeNewFolderDialog" />
      </div>
    </div>
     
    <!-- 成功消息提示 -->
    <Transition name="waves-toast">
      <div v-if="successMessage" class="waves-success-toast">
        <div class="waves-toast-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="waves-toast-content">
          <div class="waves-toast-title">操作成功</div>
          <div class="waves-toast-message">{{ successMessage }}</div>
        </div>
        <button @click="successMessage = ''" class="waves-toast-close">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </Transition>
  </div>
</template>

<script>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFilesStore } from '../stores/files'
import NavigationBar from '../components/NavigationBar.vue'
import FolderTree from '../components/FolderTree.vue'
import FileDisplay from '../components/FileDisplay.vue'
import UploadDialog from '../components/UploadDialog.vue'
import NewFolderDialog from '../components/NewFolderDialog.vue'

export default {
  name: 'FileList',
  components: {
    NavigationBar,
    FolderTree,
    FileDisplay,
    UploadDialog,
    NewFolderDialog
  },
  setup() {
    const router = useRouter()
    const filesStore = useFilesStore()
    const successMessage = ref('')
    
    const isLoading = computed(() => filesStore.isLoading)
    const error = computed(() => filesStore.error)
    const showUploadDialog = computed(() => filesStore.showUploadDialog)
    const showNewFolderDialog = computed(() => filesStore.showNewFolderDialog)
    
    const closeUploadDialog = () => {
      filesStore.closeAllDialogs()
    }
    
    const closeNewFolderDialog = () => {
      filesStore.closeAllDialogs()
    }
    
    const refreshFiles = async () => {
      await filesStore.fetchFiles()
    }
    
    const goHome = () => {
      router.push('/')
    }
    
    const showSuccessMessage = (message) => {
      successMessage.value = message
      setTimeout(() => {
        successMessage.value = ''
      }, 4000)
    }
    
    onMounted(async () => {
      await filesStore.fetchFiles()
    })
    
    return {
      isLoading,
      error,
      showUploadDialog,
      showNewFolderDialog,
      successMessage,
      closeUploadDialog,
      closeNewFolderDialog,
      refreshFiles,
      goHome,
      showSuccessMessage
    }
  }
}
</script>

<style scoped>
/* 企业级文件管理器样式 */
.waves-file-manager {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--waves-corporate-bg);
  overflow: hidden;
}

.waves-main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.waves-sidebar {
  width: 280px;
  background: #ffffff;
  overflow: hidden;
  flex-shrink: 0;
}

.waves-content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--waves-surface-primary);
  overflow: hidden;
  padding: 1rem 1.5rem 1rem 1rem;
}

.waves-file-display-container {
  flex: 1;
  overflow: hidden;
}

/* 加载状态样式 */
.waves-loading-container {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--waves-surface-primary);
}

.waves-loading-content {
  text-align: center;
  max-width: 400px;
  padding: 3rem;
}

.waves-loading-spinner {
  width: 80px;
  height: 80px;
  margin: 0 auto 2rem;
  background: linear-gradient(135deg, var(--waves-primary-500), var(--waves-primary-600));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: waves-pulse 2s ease-in-out infinite;
}

.waves-spinner-icon {
  width: 40px;
  height: 40px;
  color: white;
  animation: waves-spin 1.5s linear infinite;
}

@keyframes waves-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes waves-pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(var(--waves-primary-rgb), 0.4);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 20px rgba(var(--waves-primary-rgb), 0);
  }
}

.waves-loading-text {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--waves-text-primary);
  margin-bottom: 0.5rem;
}

.waves-loading-description {
  font-size: 1rem;
  color: var(--waves-text-secondary);
  line-height: 1.6;
}

/* 错误状态样式 */
.waves-error-container {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--waves-surface-primary);
  padding: 3rem;
}

.waves-error-content {
  text-align: center;
  max-width: 500px;
  background: var(--waves-surface-secondary);
  padding: 3rem;
  border-radius: var(--waves-radius-xl);
  border: 1px solid var(--waves-border-light);
  box-shadow: var(--waves-shadow-lg);
}

.waves-error-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 2rem;
  background: linear-gradient(135deg, var(--waves-error-500), var(--waves-error-600));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.waves-error-icon svg {
  width: 40px;
  height: 40px;
}

.waves-error-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--waves-text-primary);
  margin-bottom: 1rem;
}

.waves-error-message {
  font-size: 1rem;
  color: var(--waves-text-secondary);
  margin-bottom: 2rem;
  line-height: 1.6;
}

.waves-error-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.waves-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: var(--waves-radius-md);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  font-size: 0.875rem;
}

.waves-btn-icon {
  width: 16px;
  height: 16px;
}

.waves-btn-primary {
  background: var(--waves-primary-600);
  color: white;
}

.waves-btn-primary:hover {
  background: var(--waves-primary-700);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-md);
}

.waves-btn-secondary {
  background: var(--waves-surface-primary);
  color: var(--waves-text-primary);
  border: 1px solid var(--waves-border-light);
}

.waves-btn-secondary:hover {
  background: var(--waves-surface-secondary);
  border-color: var(--waves-primary-300);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-md);
}

/* 模态框样式 */
.waves-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: waves-fade-in 0.3s ease;
}

.waves-modal-container {
  max-width: 90vw;
  max-height: 90vh;
  overflow: auto;
  animation: waves-scale-in 0.3s ease;
}

@keyframes waves-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes waves-scale-in {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

/* 成功提示样式 */
.waves-success-toast {
  position: fixed;
  top: 2rem;
  right: 2rem;
  background: var(--waves-surface-primary);
  border: 1px solid var(--waves-success-300);
  border-left: 4px solid var(--waves-success-500);
  border-radius: var(--waves-radius-lg);
  box-shadow: var(--waves-shadow-xl);
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  max-width: 400px;
  z-index: 1100;
  backdrop-filter: blur(8px);
}

.waves-toast-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--waves-success-500), var(--waves-success-600));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.waves-toast-icon svg {
  width: 20px;
  height: 20px;
}

.waves-toast-content {
  flex: 1;
  min-width: 0;
}

.waves-toast-title {
  font-weight: 600;
  color: var(--waves-text-primary);
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
}

.waves-toast-message {
  color: var(--waves-text-secondary);
  font-size: 0.8rem;
  line-height: 1.4;
}

.waves-toast-close {
  width: 24px;
  height: 24px;
  border: none;
  background: none;
  color: var(--waves-text-secondary);
  cursor: pointer;
  border-radius: var(--waves-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.waves-toast-close:hover {
  background: var(--waves-surface-secondary);
  color: var(--waves-text-primary);
}

.waves-toast-close svg {
  width: 14px;
  height: 14px;
}

/* Toast 动画 */
.waves-toast-enter-active,
.waves-toast-leave-active {
  transition: all 0.4s ease;
}

.waves-toast-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.waves-toast-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .waves-sidebar {
    width: 240px;
  }
  
  .waves-success-toast {
    right: 1rem;
    left: 1rem;
    max-width: none;
  }
}

@media (max-width: 768px) {
  .waves-main-content {
    flex-direction: column;
  }
  
  .waves-sidebar {
    width: 100%;
    height: 200px;
    border-right: none;
  }
  
  .waves-loading-content,
  .waves-error-content {
    padding: 2rem;
  }
  
  .waves-error-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .waves-success-toast {
    top: 1rem;
    right: 1rem;
    left: 1rem;
    padding: 1rem;
  }
  
  .waves-modal-container {
    max-width: 95vw;
    margin: 1rem;
  }
}

@media (max-width: 480px) {
  .waves-sidebar {
    height: 150px;
  }
  
  .waves-loading-spinner,
  .waves-error-icon {
    width: 60px;
    height: 60px;
  }
  
  .waves-spinner-icon,
  .waves-error-icon svg {
    width: 30px;
    height: 30px;
  }
  
  .waves-loading-text,
  .waves-error-title {
    font-size: 1.125rem;
  }
  
  .waves-btn {
    padding: 0.625rem 1.25rem;
    font-size: 0.8rem;
  }
  
  .waves-success-toast {
    padding: 0.75rem;
  }
  
  .waves-toast-icon {
    width: 32px;
    height: 32px;
  }
  
  .waves-toast-icon svg {
    width: 16px;
    height: 16px;
  }
}

/* 滚动条样式 */
.waves-modal-container::-webkit-scrollbar {
  width: 8px;
}

.waves-modal-container::-webkit-scrollbar-track {
  background: var(--waves-surface-secondary);
  border-radius: var(--waves-radius-sm);
}

.waves-modal-container::-webkit-scrollbar-thumb {
  background: var(--waves-border-light);
  border-radius: var(--waves-radius-sm);
}

.waves-modal-container::-webkit-scrollbar-thumb:hover {
  background: var(--waves-primary-400);
}
</style>