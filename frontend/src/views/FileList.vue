<template>
  <div class="file-manager">
    <!-- 顶部导航栏 -->
    <NavigationBar />
    
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧目录树 -->
      <FolderTree />
      
      <!-- 右侧文件显示区域 -->
      <div class="file-content">
        <!-- 加载状态 -->
       <div v-if="isLoading" class="loading">
         <div class="loading-spinner"></div>
         <div class="loading-text">加载中...</div>
       </div>
       
       <!-- 错误状态 -->
       <div v-else-if="error" class="error">
         <div class="error-icon">⚠️</div>
         <div class="error-text">{{ error }}</div>
         <button @click="refreshFiles" class="retry-btn">重试</button>
       </div>
        
        <!-- 文件显示 -->
        <FileDisplay v-else />
      </div>
    </div>
     
     <!-- 上传文件对话框 -->
     <UploadDialog v-if="showUploadDialog" @close="closeUploadDialog" />
     
     <!-- 新建文件夹对话框 -->
     <NewFolderDialog v-if="showNewFolderDialog" @close="closeNewFolderDialog" />
     
     <!-- 成功消息提示 -->
     <div v-if="successMessage" class="success-toast">
       {{ successMessage }}
     </div>
   </div>
 </template>

<script>
 import { computed, ref, onMounted } from 'vue'
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
     
     const showSuccessMessage = (message) => {
       successMessage.value = message
       setTimeout(() => {
         successMessage.value = ''
       }, 3000)
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
       showSuccessMessage
     }
   }
 }
 </script>

<style scoped>
.file-manager {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.file-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #666;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #d32f2f;
  background: #ffebee;
  margin: 20px;
  border-radius: 8px;
  border: 1px solid #ffcdd2;
}

.error-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.error-text {
  font-size: 16px;
  margin-bottom: 16px;
}

.retry-btn {
  padding: 8px 16px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.retry-btn:hover {
  background: #40a9ff;
}

.success-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #52c41a;
  color: white;
  padding: 12px 20px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-dialog {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #262626;
}

.modal-body {
  padding: 20px;
  color: #595959;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #e8e8e8;
  background: #fafafa;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>