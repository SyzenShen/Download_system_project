<template>
  <div class="file-upload">
    <div class="card">
      <div class="card-header">
        <h2 class="card-title text-white">上传文件</h2>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-error">
          {{ error }}
        </div>
        
        <div v-if="successMessage" class="alert alert-success">
          {{ successMessage }}
        </div>
        
        <!-- 拖拽上传区域 -->
        <div
          class="upload-area"
          :class="{ dragover: isDragOver, 'has-file': selectedFile }"
          @click="triggerFileInput"
          @dragover.prevent="handleDragOver"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="handleDrop"
        >
          <div v-if="!selectedFile" class="upload-placeholder">
            <div class="upload-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.89 22 5.99 22H18C19.1 22 20 21.1 20 20V8L14 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M14 2V8H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 18V12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M9 15L12 12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3 class="upload-title">选择文件或拖拽到此处</h3>
            <p class="upload-subtitle">
              支持所有文件格式，单个文件最大 {{ maxUploadGB }}GB
            </p>
            <button type="button" class="btn btn-primary upload-btn" @click.stop="triggerFileInput">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 8px;">
                <path d="M21 15V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M7 10L12 15L17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 15V3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              选择文件
            </button>
          </div>
          
          <div v-else class="upload-preview">
            <div class="file-preview-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.89 22 5.99 22H18C19.1 22 20 21.1 20 20V8L14 2Z" fill="currentColor"/>
                <path d="M14 2V8H20" fill="#ffffff"/>
              </svg>
            </div>
            <h3 class="file-name">{{ selectedFile.name }}</h3>
            <p class="file-size">
              大小: {{ formatFileSize(selectedFile.size) }}
            </p>
            <div class="upload-actions">
              <button @click.stop="clearFile" class="btn btn-secondary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 8px;">
                  <path d="M3 6H5H21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6H19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                重新选择
              </button>
              <button @click.stop="uploadFile" class="btn btn-primary" :disabled="isLoading">
                <span v-if="isLoading" class="loading"></span>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-right: 8px;">
                  <path d="M21 15V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M17 8L12 3L7 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M12 3V15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ isLoading ? '上传中...' : '开始上传' }}
              </button>
              <button v-if="!uploadPaused" @click.stop="pauseUpload" class="btn btn-secondary" :disabled="!isLoading" style="margin-left: 8px;">
                暂停
              </button>
              <button v-else @click.stop="resumeUpload" class="btn btn-secondary" :disabled="!selectedFile" style="margin-left: 8px;">
                继续
              </button>
              <button @click.stop="cancelUpload" class="btn btn-danger" :disabled="!isLoading" style="margin-left: 8px;">
                取消
              </button>
            </div>
          </div>
        </div>
        
        <!-- 上传进度 -->
        <div v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
          <div class="progress">
            <div class="progress-bar" :style="{ width: uploadProgress + '%' }"></div>
          </div>
          <div class="progress-text">
            <span>上传进度: {{ uploadProgress }}%</span>
            <span class="progress-speed" v-if="uploadSpeed">{{ uploadSpeed }}</span>
          </div>
        </div>
        
        <!-- 隐藏的文件输入 -->
        <input
          ref="fileInput"
          type="file"
          style="display: none;"
          @change="handleFileSelect"
        />
        
        <!-- 上传方式选择 -->
        <div class="form-group" style="margin-top: 20px;">
          <label class="form-label text-white">上传方式</label>
          <select v-model="uploadMethod" class="form-control">
            <option value="Vue Frontend">Vue 前端上传</option>
            <option value="Ajax Upload">Ajax 上传</option>
            <option value="Form Upload">表单上传</option>
          </select>
        </div>
        
        <!-- 最近上传的文件 -->
        <div v-if="recentFiles.length > 0" style="margin-top: 30px;">
          <h3 class="text-white" style="margin-bottom: 15px;">最近上传</h3>
          <div class="recent-files">
            <div
              v-for="file in recentFiles"
              :key="file.id"
              class="recent-file-item"
            >
              <span class="file-icon">📄</span>
              <span class="file-name">{{ getDisplayName(file) }}</span>
              <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
              <router-link to="/files" class="btn btn-secondary" style="padding: 2px 8px; font-size: 12px;">
                查看全部
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFilesStore } from '../stores/files'

export default {
  name: 'FileUpload',
  setup() {
    const router = useRouter()
    const filesStore = useFilesStore()
    
    const fileInput = ref(null)
    const selectedFile = ref(null)
    const isDragOver = ref(false)
    const uploadMethod = ref('Vue Frontend')
    const successMessage = ref('')
    const maxUploadGB = ref(100)
    
    const isLoading = computed(() => filesStore.isLoading)
    const error = computed(() => filesStore.error)
    const uploadProgress = computed(() => filesStore.uploadProgress)
    const uploadPaused = computed(() => filesStore.uploadPaused)
    const recentFiles = computed(() => filesStore.files.slice(0, 3))
    
    const triggerFileInput = () => {
      if (!selectedFile.value) {
        fileInput.value?.click()
      }
    }
    
    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        if (!validateSize(file)) return
        selectedFile.value = file
      }
    }
    
    const handleDragOver = (event) => {
      isDragOver.value = true
    }
    
    const handleDragLeave = (event) => {
      isDragOver.value = false
    }
    
    const handleDrop = (event) => {
      isDragOver.value = false
      const files = event.dataTransfer.files
      if (files.length > 0) {
        if (!validateSize(files[0])) return
        selectedFile.value = files[0]
      }
    }
    
    const clearFile = () => {
      selectedFile.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }
    
    const uploadFile = async () => {
      if (!selectedFile.value) return
      if (!validateSize(selectedFile.value)) return
      
      const result = await filesStore.uploadFile(selectedFile.value, uploadMethod.value, filesStore.currentFolderId)
      
      if (result.success) {
        successMessage.value = result.message
        clearFile()
        setTimeout(() => {
          successMessage.value = ''
        }, 3000)
      }
    }

    const pauseUpload = () => {
      filesStore.pauseUpload()
    }
    const resumeUpload = async () => {
      const result = await filesStore.resumeUpload()
      if (result?.success) {
        successMessage.value = result.message
        clearFile()
        setTimeout(() => { successMessage.value = '' }, 3000)
      } else if (result?.error) {
        filesStore.error = result.error
      }
    }

    const cancelUpload = () => {
      filesStore.cancelUpload()
      clearFile()
    }
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    const getFileName = (filePath) => {
      return filePath ? filePath.split('/').pop() : '未知文件'
    }
    
    const getDisplayName = (file) => {
      // 优先使用后端保存的原始文件名，其次使用序列化的文件名，最后兜底从路径提取
      return file?.original_filename || file?.file_name || getFileName(file?.file)
    }

    const validateSize = (file) => {
      const maxBytes = maxUploadGB.value * 1024 * 1024 * 1024
      if (file.size > maxBytes) {
        filesStore.error = `文件过大，最大允许 ${maxUploadGB.value}GB`
        return false
      }
      return true
    }
    
    onMounted(() => {
      // 获取最近上传的文件
      filesStore.fetchFiles()
    })
    
    return {
      fileInput,
      selectedFile,
      isDragOver,
      uploadMethod,
      successMessage,
      isLoading,
      error,
      uploadProgress,
      uploadPaused,
      recentFiles,
      maxUploadGB,
      triggerFileInput,
      handleFileSelect,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      clearFile,
      uploadFile,
      pauseUpload,
      resumeUpload,
      cancelUpload,
      formatFileSize,
      getFileName,
      getDisplayName
    }
  }
}
</script>

<style scoped>
.upload-icon { color: var(--brand-blue); }
.upload-area {
  border: 2px dashed #d1d1d1;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  background-color: #fafafa;
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.upload-area:hover {
  border-color: var(--brand-blue);
  background-color: #f8f9fa;
}

.upload-area.dragover {
  border-color: var(--brand-blue);
  background-color: #e3f2fd;
  transform: scale(1.02);
}

.upload-area.has-file {
  border-color: #107c10;
  background-color: #f3f9f3;
}

.upload-placeholder,
.upload-preview {
  text-align: center;
}

.upload-icon {
  margin-bottom: 20px;
  opacity: 0.8;
  transition: opacity 0.3s ease;
}

.upload-area:hover .upload-icon {
  opacity: 1;
}

.upload-title {
  margin-bottom: 12px;
  color: #323130;
  font-size: 20px;
  font-weight: 600;
}

.upload-subtitle {
  color: #605e5c;
  margin-bottom: 24px;
  font-size: 14px;
  line-height: 1.5;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.file-preview-icon {
  margin-bottom: 16px;
}

.file-name {
  margin-bottom: 8px;
  color: #323130;
  font-size: 18px;
  font-weight: 600;
  word-break: break-all;
}

.file-size {
  color: #605e5c;
  margin-bottom: 20px;
  font-size: 14px;
}

.upload-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.upload-progress {
  margin-top: 24px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e1e5e9;
}

.progress {
  width: 100%;
  height: 12px;
  background-color: #e1e5e9;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--brand-blue) 0%, var(--brand-blue-hover) 100%);
  transition: width 0.3s ease;
  border-radius: 6px;
  position: relative;
}

.progress-bar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.3) 50%,
    transparent 100%
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #605e5c;
}

.progress-speed {
  font-size: 12px;
  color: #8a8886;
}

.recent-files {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-file-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background-color: white;
  border-radius: 8px;
  border: 1px solid #e1e5e9;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.recent-file-item:hover {
  border-color: var(--brand-blue);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
  transform: translateY(-1px);
}

.file-icon {
  font-size: 20px;
  margin-right: 16px;
  opacity: 0.8;
}

.file-name {
  flex: 1;
  font-weight: 500;
  color: #323130;
  margin-right: 12px;
}

.file-size {
  color: #8a8886;
  font-size: 12px;
  margin-right: 12px;
  min-width: 60px;
  text-align: right;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .upload-area {
    padding: 24px 16px;
  }
  
  .upload-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .upload-actions .btn {
    width: 100%;
    max-width: 200px;
  }
  
  .recent-file-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .file-name,
  .file-size {
    margin-right: 0;
  }
}
</style>
