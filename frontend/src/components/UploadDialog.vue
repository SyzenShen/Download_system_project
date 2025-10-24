<template>
  <div class="waves-upload-dialog">
    <div class="waves-dialog-container">
      <!-- 对话框头部 -->
      <div class="waves-dialog-header">
        <div class="waves-header-content">
          <div class="waves-header-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 18V12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M9 15L12 12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="waves-header-text">
            <h3 class="waves-dialog-title">文件上传</h3>
            <p class="waves-dialog-subtitle">选择并上传您的文件到当前文件夹</p>
          </div>
        </div>
        <button @click="$emit('close')" class="waves-close-btn">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      
      <!-- 对话框主体 -->
      <div class="waves-dialog-body">
        <!-- 上传区域 -->
        <div 
          class="waves-upload-zone" 
          :class="{ 'waves-drag-over': isDragOver, 'waves-has-files': selectedFiles.length > 0 }"
          @drop="handleDrop" 
          @dragover.prevent="handleDragOver" 
          @dragleave.prevent="handleDragLeave"
          @click="selectFiles"
        >
          <input
            ref="fileInput"
            type="file"
            multiple
            @change="handleFileSelect"
            style="display: none"
          />
          
          <div class="waves-upload-content">
            <div class="waves-upload-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M17 8L12 3L7 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 3V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h4 class="waves-upload-title">拖拽文件到此处或点击选择</h4>
            <p class="waves-upload-description">支持多个文件同时上传，单个文件最大 100GB</p>
            

          </div>
        </div>
        
        <!-- 简约进度条 - 在文件列表上方 -->
        <div v-if="uploading" class="simple-upload-progress">
          <div class="progress-info">
            <span class="progress-label">正在上传文件...</span>
            <span class="progress-percentage">{{ uploadProgress }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
        </div>
        
        <!-- 文件列表 -->
        <div v-if="selectedFiles.length > 0" class="waves-file-list">
          <div class="waves-list-header">
            <h4 class="waves-list-title">
              <svg class="waves-list-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              待上传文件 ({{ selectedFiles.length }})
            </h4>
            <button @click="clearAllFiles" class="waves-clear-btn">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 6H5H21M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              清空
            </button>
          </div>
          
          <div class="waves-file-items">
            <div v-for="(file, index) in selectedFiles" :key="index" class="waves-file-item">
              <div class="waves-file-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="waves-file-info">
                <div class="waves-file-name">{{ file.name }}</div>
                <div class="waves-file-meta">
                  <span class="waves-file-size">{{ formatFileSize(file.size) }}</span>
                  <span class="waves-file-type">{{ getFileType(file.name) }}</span>
                </div>
              </div>
              <button @click="removeFile(index)" class="waves-remove-btn">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 对话框底部 -->
      <div class="waves-dialog-footer">
        <button @click="$emit('close')" class="waves-btn waves-btn-secondary">
          <svg class="waves-btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          取消
        </button>
        <button 
          @click="uploadFiles" 
          class="waves-btn waves-btn-primary" 
          :disabled="selectedFiles.length === 0 || uploading"
        >
          <svg v-if="!uploading" class="waves-btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M17 8L12 3L7 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 3V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <div v-else class="waves-loading-spinner">
            <svg class="waves-spinner" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2V6M12 18V22M4.93 4.93L7.76 7.76M16.24 16.24L19.07 19.07M2 12H6M18 12H22M4.93 19.07L7.76 16.24M16.24 7.76L19.07 4.93" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          {{ uploading ? '上传中...' : '开始上传' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useFilesStore } from '../stores/files'

export default {
  name: 'UploadDialog',
  emits: ['close'],
  setup(props, { emit }) {
    const filesStore = useFilesStore()
    const selectedFiles = ref([])
    const uploading = ref(false)
    const uploadProgress = ref(0)
    const isDragOver = ref(false)
    
    const currentFolderId = computed(() => filesStore.currentFolderId)
    
    const fileInput = ref(null)
    
    // 监听store中的上传状态
    watch(() => filesStore.isLoading, (isLoading) => {
      if (!isLoading && uploading.value) {
        // 上传完成，重置状态
        uploading.value = false
        uploadProgress.value = 0
      }
    })
    
    const selectFiles = () => {
      fileInput.value.click()
    }
    
    const handleFileSelect = (event) => {
      const files = Array.from(event.target.files)
      selectedFiles.value = [...selectedFiles.value, ...files]
    }
    
    const handleDragOver = (event) => {
      event.preventDefault()
      isDragOver.value = true
    }
    
    const handleDragLeave = (event) => {
      event.preventDefault()
      isDragOver.value = false
    }
    
    const handleDrop = (event) => {
      event.preventDefault()
      isDragOver.value = false
      const files = Array.from(event.dataTransfer.files)
      selectedFiles.value = [...selectedFiles.value, ...files]
    }
    
    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1)
    }
    
    const clearAllFiles = () => {
      selectedFiles.value = []
    }
    
    const uploadFiles = async () => {
      if (selectedFiles.value.length === 0) return
      
      uploading.value = true
      uploadProgress.value = 0
      
      try {
        // 计算总文件大小用于准确的进度计算
        const totalSize = selectedFiles.value.reduce((sum, file) => sum + file.size, 0)
        let uploadedSize = 0
        
        for (let i = 0; i < selectedFiles.value.length; i++) {
          const file = selectedFiles.value[i]
          
          // 设置当前文件的进度监听
          const initialUploadedSize = uploadedSize
          const progressWatcher = watch(() => filesStore.uploadProgress, (fileProgress) => {
            if (uploading.value) {
              // 计算当前文件已上传的字节数
              const currentFileUploaded = (fileProgress / 100) * file.size
              // 计算总体进度
              const totalUploaded = initialUploadedSize + currentFileUploaded
              uploadProgress.value = Math.round((totalUploaded / totalSize) * 100)
            }
          })
          
          await filesStore.uploadFile(
            file,
            'Vue Frontend',
            currentFolderId.value
          )
          
          // 停止监听当前文件进度
          progressWatcher()
          
          // 更新已上传大小
          uploadedSize += file.size
          uploadProgress.value = Math.round((uploadedSize / totalSize) * 100)
        }
        
        await filesStore.fetchFiles(currentFolderId.value)
        emit('close')
      } catch (error) {
        console.error('上传失败:', error)
        alert('上传失败: ' + error.message)
      } finally {
        uploading.value = false
        uploadProgress.value = 0
      }
    }
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    const getFileType = (filename) => {
      const ext = filename.split('.').pop().toLowerCase()
      const types = {
        'pdf': 'PDF文档',
        'doc': 'Word文档',
        'docx': 'Word文档',
        'xls': 'Excel表格',
        'xlsx': 'Excel表格',
        'ppt': 'PowerPoint',
        'pptx': 'PowerPoint',
        'txt': '文本文件',
        'jpg': '图片',
        'jpeg': '图片',
        'png': '图片',
        'gif': '图片',
        'mp4': '视频',
        'avi': '视频',
        'mov': '视频',
        'mp3': '音频',
        'wav': '音频',
        'zip': '压缩包',
        'rar': '压缩包'
      }
      return types[ext] || '未知类型'
    }
    
    return {
      selectedFiles,
      uploading,
      uploadProgress,
      isDragOver,
      currentFolderId,
      fileInput,
      selectFiles,
      handleFileSelect,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      removeFile,
      clearAllFiles,
      uploadFiles,
      formatFileSize,
      getFileType
    }
  }
}
</script>

<style scoped>
/* 企业级上传对话框样式 */
.waves-upload-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: transparent;
  backdrop-filter: none;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.waves-dialog-container {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  max-width: 600px;
  width: 90vw;
  max-height: 90vh;
  overflow: hidden;
  animation: waves-scale-in 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  border: 1px solid #e5e7eb;
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
    transform: scale(0.8) translateY(20px);
    opacity: 0;
  }
  50% {
    transform: scale(0.95) translateY(10px);
    opacity: 0.8;
  }
  to {
    transform: scale(1) translateY(0);
    opacity: 1;
  }
}

/* 对话框头部 */
.waves-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 2rem;
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  position: relative;
}

.waves-header-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.waves-header-icon {
  width: 40px;
  height: 40px;
  background: var(--waves-primary-500);
  border-radius: var(--waves-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: var(--waves-shadow-sm);
}

.waves-header-icon svg {
  width: 20px;
  height: 20px;
}

.waves-header-text {
  flex: 1;
}

.waves-dialog-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.25rem 0;
}

.waves-dialog-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.4;
}

.waves-close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #6b7280;
}

.waves-close-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

.waves-close-btn svg {
  width: 16px;
  height: 16px;
}

/* 对话框主体 */
.waves-dialog-body {
  padding: 2rem;
  max-height: 60vh;
  overflow-y: auto;
  background: #ffffff;
}

/* 上传区域 */
.waves-upload-zone {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 3rem 2rem;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  background: #f9fafb;
  position: relative;
  overflow: hidden;
}

.waves-upload-zone::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, transparent 30%, rgba(var(--waves-primary-rgb), 0.02) 50%, transparent 70%);
  pointer-events: none;
}

.waves-upload-zone:hover {
  border-color: #3b82f6;
  background: #eff6ff;
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-lg);
}

.waves-upload-zone.waves-drag-over {
  border-color: #3b82f6;
  background: #dbeafe;
  transform: scale(1.02);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.waves-upload-zone.waves-has-files {
  border-color: #10b981;
  background: #ecfdf5;
}

.waves-upload-content {
  position: relative;
  z-index: 1;
}

.waves-upload-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.waves-upload-icon svg {
  width: 40px;
  height: 40px;
}

.waves-upload-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 0.5rem 0;
}

.waves-upload-description {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 2rem 0;
  line-height: 1.6;
}



/* 文件列表 */
.waves-file-list {
  margin-top: 2rem;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.waves-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: #eff6ff;
  border-bottom: 1px solid #e5e7eb;
}

.waves-list-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.waves-list-icon {
  width: 16px;
  height: 16px;
  color: #3b82f6;
}

.waves-clear-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e5e7eb;
  background: #ffffff;
  border-radius: 6px;
  font-size: 0.8rem;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.3s ease;
}

.waves-clear-btn:hover {
  background: #fef2f2;
  border-color: #fca5a5;
  color: #dc2626;
}

.waves-clear-btn svg {
  width: 14px;
  height: 14px;
}

.waves-file-items {
  max-height: 200px;
  overflow-y: auto;
}

.waves-file-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.waves-file-item:last-child {
  border-bottom: none;
}

.waves-file-item:hover {
  background: #f0f9ff;
}

.waves-file-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3b82f6;
  flex-shrink: 0;
}

.waves-file-icon svg {
  width: 16px;
  height: 16px;
}

.waves-file-info {
  flex: 1;
  min-width: 0;
}

.waves-file-name {
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.875rem;
}

.waves-file-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.waves-remove-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: #fee2e2;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #dc2626;
  flex-shrink: 0;
}

.waves-remove-btn:hover {
  background: #fecaca;
  transform: scale(1.1);
}

.waves-remove-btn svg {
  width: 12px;
  height: 12px;
}

/* 简约上传进度条 */
.simple-upload-progress {
  margin: 1rem 0;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.progress-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #475569;
}

.progress-percentage {
  font-size: 0.875rem;
  font-weight: 600;
  color: #3b82f6;
}

.progress-bar {
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #06b6d4);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* 对话框底部 */
.waves-dialog-footer {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding: 2rem;
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
}

.waves-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  font-size: 0.875rem;
  min-width: 120px;
  justify-content: center;
}

.waves-btn-icon {
  width: 16px;
  height: 16px;
}

.waves-btn-primary {
  background: #3b82f6;
  color: white;
}

.waves-btn-primary:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.waves-btn-primary:disabled {
  background: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.waves-btn-secondary {
  background: #ffffff;
  color: #374151;
  border: 1px solid #d1d5db;
}

.waves-btn-secondary:hover {
  background: #f9fafb;
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.waves-loading-spinner {
  width: 16px;
  height: 16px;
}

/* 滚动条样式 */
.waves-dialog-body::-webkit-scrollbar,
.waves-file-items::-webkit-scrollbar {
  width: 8px;
}

.waves-dialog-body::-webkit-scrollbar-track,
.waves-file-items::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 4px;
}

.waves-dialog-body::-webkit-scrollbar-thumb,
.waves-file-items::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.waves-dialog-body::-webkit-scrollbar-thumb:hover,
.waves-file-items::-webkit-scrollbar-thumb:hover {
  background: #60a5fa;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .waves-dialog-container {
    width: 95vw;
    max-height: 95vh;
  }
  
  .waves-dialog-header,
  .waves-dialog-body,
  .waves-dialog-footer {
    padding: 1.5rem;
  }
  
  .waves-upload-zone {
    padding: 2rem 1rem;
  }
  
  .waves-upload-icon {
    width: 60px;
    height: 60px;
  }
  
  .waves-upload-icon svg {
    width: 30px;
    height: 30px;
  }
  

  
  .waves-dialog-footer {
    flex-direction: column;
  }
  
  .waves-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .waves-dialog-header {
    padding: 1rem;
  }
  
  .waves-header-icon {
    width: 40px;
    height: 40px;
  }
  
  .waves-header-icon svg {
    width: 20px;
    height: 20px;
  }
  
  .waves-dialog-title {
    font-size: 1.125rem;
  }
  
  .waves-dialog-subtitle {
    font-size: 0.8rem;
  }
  
  .waves-upload-zone {
    padding: 1.5rem 1rem;
  }
  
  .waves-upload-title {
    font-size: 1rem;
  }
  
  .waves-upload-description {
    font-size: 0.8rem;
  }
}
</style>