<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-dialog" @click.stop>
      <div class="modal-header">
        <h3>上传文件</h3>
      </div>
      <div class="modal-body">
        <div class="upload-area" @drop="handleDrop" @dragover.prevent @dragenter.prevent>
          <input
            ref="fileInput"
            type="file"
            multiple
            @change="handleFileSelect"
            style="display: none"
          />
          <div class="upload-content">
            <div class="upload-icon">📁</div>
            <p class="upload-text">拖拽文件到此处或点击选择文件</p>
            <button @click="selectFiles" class="upload-btn">选择文件</button>
          </div>
        </div>
        
        <div v-if="selectedFiles.length > 0" class="file-list">
          <h4>待上传文件：</h4>
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">{{ formatFileSize(file.size) }}</span>
            <button @click="removeFile(index)" class="remove-btn">×</button>
          </div>
        </div>
        
        <div v-if="uploading" class="upload-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
          </div>
          <p class="progress-text">{{ uploadProgress }}% 已上传</p>
        </div>
      </div>
      <div class="modal-footer">
        <button @click="$emit('close')" class="btn btn-secondary">取消</button>
        <button 
          @click="uploadFiles" 
          class="btn btn-primary" 
          :disabled="selectedFiles.length === 0 || uploading"
        >
          {{ uploading ? '上传中...' : '开始上传' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useFilesStore } from '../stores/files'

export default {
  name: 'UploadDialog',
  emits: ['close'],
  setup(props, { emit }) {
    const filesStore = useFilesStore()
    const selectedFiles = ref([])
    const uploading = ref(false)
    const uploadProgress = ref(0)
    
    const currentFolderId = computed(() => filesStore.currentFolderId)
    
    const fileInput = ref(null)
    
    const selectFiles = () => {
      fileInput.value.click()
    }
    
    const handleFileSelect = (event) => {
      const files = Array.from(event.target.files)
      selectedFiles.value = [...selectedFiles.value, ...files]
    }
    
    const handleDrop = (event) => {
      event.preventDefault()
      const files = Array.from(event.dataTransfer.files)
      selectedFiles.value = [...selectedFiles.value, ...files]
    }
    
    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1)
    }
    
    const uploadFiles = async () => {
      if (selectedFiles.value.length === 0) return
      
      uploading.value = true
      uploadProgress.value = 0
      
      try {
        for (let i = 0; i < selectedFiles.value.length; i++) {
          const file = selectedFiles.value[i]
          await filesStore.uploadFile(
            file,
            'Vue Frontend',
            currentFolderId.value
          )
          // 更新进度
          uploadProgress.value = Math.round(((i + 1) / selectedFiles.value.length) * 100)
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
    
    return {
      selectedFiles,
      uploading,
      uploadProgress,
      currentFolderId,
      fileInput,
      selectFiles,
      handleFileSelect,
      handleDrop,
      removeFile,
      uploadFiles,
      formatFileSize
    }
  }
}
</script>

<style scoped>
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
  max-height: 60vh;
  overflow-y: auto;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #e8e8e8;
  background: #fafafa;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  transition: border-color 0.3s ease;
  cursor: pointer;
}

.upload-area:hover {
  border-color: #1890ff;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-icon {
  font-size: 48px;
  opacity: 0.6;
}

.upload-text {
  margin: 0;
  color: #595959;
  font-size: 14px;
}

.upload-btn {
  padding: 8px 16px;
  background: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.upload-btn:hover {
  background: #40a9ff;
}

.file-list {
  margin-top: 20px;
}

.file-list h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #262626;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
  margin-bottom: 8px;
}

.file-name {
  flex: 1;
  font-size: 14px;
  color: #262626;
  margin-right: 12px;
  word-break: break-all;
}

.file-size {
  font-size: 12px;
  color: #8c8c8c;
  margin-right: 12px;
}

.remove-btn {
  width: 20px;
  height: 20px;
  border: none;
  background: #ff4d4f;
  color: white;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover {
  background: #ff7875;
}

.upload-progress {
  margin-top: 20px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #1890ff;
  transition: width 0.3s ease;
}

.progress-text {
  margin: 8px 0 0 0;
  font-size: 12px;
  color: #595959;
  text-align: center;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #40a9ff;
}

.btn-primary:disabled {
  background: #d9d9d9;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #595959;
}

.btn-secondary:hover {
  background: #e6f7ff;
}
</style>