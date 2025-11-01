<template>
  <div class="file-upload waves-corporate-bg">
    <!-- 简约进度条 - 移到卡片上方 -->
    <div v-if="isUploading || uploadProgress > 0" class="simple-progress-bar">
      <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
      <span class="progress-text">{{ uploadProgress.toFixed(0) }}%</span>
    </div>

    <div class="upload-container">
      <!-- 头部区域 -->
      <div class="upload-header">
        <h1 class="upload-title waves-text-corporate">文件上传中心</h1>
        <p class="upload-subtitle waves-text-light">安全、快速、可靠的企业级文件上传服务</p>
      </div>

      <!-- 主要内容区域 -->
      <div class="upload-content">
        <!-- 上传区域 -->
        <div 
          class="upload-area waves-upload-zone"
          :class="{ 'waves-upload-active': isDragOver, 'has-file': selectedFile }"
          @click="triggerFileInput"
          @dragover.prevent="handleDragOver"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="handleDrop"
        >
          <!-- 文件选择状态 -->
          <div v-if="!selectedFile" class="upload-placeholder">
            <i class="fas fa-cloud-upload-alt fa-4x waves-upload-icon"></i>
            <h3 class="upload-zone-title waves-text-corporate">拖拽文件到此处或点击选择</h3>
            <p class="upload-zone-subtitle waves-text-light">支持多种文件格式，单个文件最大 100GB</p>
            
            <!-- 功能标签 -->
            <div class="upload-features">
              <div class="feature-tag">
                <i class="fas fa-shield-alt feature-icon"></i>
                <span>安全加密</span>
              </div>
              <div class="feature-tag">
                <i class="fas fa-bolt feature-icon"></i>
                <span>快速上传</span>
              </div>
              <div class="feature-tag">
                <i class="fas fa-chart-line feature-icon"></i>
                <span>实时进度</span>
              </div>
            </div>

            <button class="waves-btn btn-primary" @click.stop="triggerFileInput">
              <i class="fas fa-folder-open"></i>
              选择文件
            </button>
          </div>

          <!-- 文件预览状态 -->
          <div v-else class="upload-preview waves-file-preview">
            <div class="file-preview-header">
              <i class="fas fa-file-alt fa-3x waves-file-icon"></i>
              <div class="file-info">
                <!-- 进度条 - 在文件名称上方 -->
                <div v-if="isUploading || uploadProgress > 0" class="file-progress-bar">
                  <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
                  <span class="progress-text">{{ uploadProgress.toFixed(0) }}%</span>
                </div>
                <h4 class="file-name waves-text-corporate">{{ selectedFile.name }}</h4>
                <p class="file-size waves-text-light">{{ formatFileSize(selectedFile.size) }}</p>
                <div class="file-status">
                  <span class="status-badge ready">准备上传</span>
                </div>
              </div>
            </div>

            <div class="upload-actions">
              <button class="waves-btn btn-secondary" @click.stop="triggerFileInput">
                <i class="fas fa-exchange-alt"></i>
                重新选择
              </button>
              <button 
                class="waves-btn btn-success" 
                @click.stop="startUpload"
                :disabled="isUploading"
              >
                <i v-if="isUploading" class="waves-loading-spinner"></i>
                <i v-else class="fas fa-upload"></i>
                {{ isUploading ? '上传中...' : '开始上传' }}
              </button>
              <button 
                v-if="isUploading && !isPaused" 
                class="waves-btn btn-warning" 
                @click.stop="pauseUpload"
              >
                <i class="fas fa-pause"></i>
                暂停
              </button>
              <button 
                v-if="isUploading && isPaused" 
                class="waves-btn btn-success" 
                @click.stop="resumeUpload"
              >
                <i class="fas fa-play"></i>
                继续
              </button>
              <button 
                v-if="isUploading" 
                class="waves-btn btn-danger" 
                @click.stop="cancelUpload"
              >
                <i class="fas fa-times"></i>
                取消
              </button>
            </div>
          </div>
        </div>

        <!-- 上传设置区域 -->
        <div class="waves-settings-section">
          <h3 class="settings-title">
            <i class="fas fa-cog settings-icon"></i>
            上传设置
          </h3>
          <div class="settings-grid">
            <div class="setting-item">
              <label class="setting-label">文件夹</label>
              <select v-model="uploadFolder" class="setting-input">
                <option value="">根目录</option>
                <option value="documents">文档</option>
                <option value="images">图片</option>
                <option value="videos">视频</option>
              </select>
            </div>
            <div class="setting-item">
              <label class="setting-label">压缩质量</label>
              <select v-model="compressionLevel" class="setting-input">
                <option value="none">无压缩</option>
                <option value="low">低压缩</option>
                <option value="medium">中等压缩</option>
                <option value="high">高压缩</option>
              </select>
            </div>
            <div class="setting-item">
              <label class="setting-label">上传完成后</label>
              <select v-model="afterUpload" class="setting-input">
                <option value="stay">停留在此页面</option>
                <option value="redirect">跳转到文件列表</option>
                <option value="download">自动下载</option>
              </select>
            </div>
          </div>
        </div>

        <!-- 最近上传文件 -->
        <div class="waves-recent-section">
          <h3 class="recent-title">
            <i class="fas fa-history recent-icon"></i>
            最近上传
          </h3>
          <div class="recent-files">
            <div 
              v-for="file in recentFiles" 
              :key="file.id" 
              class="recent-file-item"
              @click="viewFile(file)"
            >
              <i class="fas fa-file-alt fa-lg recent-file-icon"></i>
              <div class="recent-file-info">
                <div class="recent-file-name">{{ file.name }}</div>
                <div class="recent-file-meta">
                  <span>{{ formatFileSize(file.size) }}</span>
                  <span>{{ formatDate(file.uploadDate) }}</span>
                </div>
              </div>
              <div class="recent-file-actions">
                <button class="action-btn" @click.stop="downloadFile(file)" title="下载">
                  <i class="fas fa-download"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 隐藏的文件输入 -->
    <input 
      ref="fileInput" 
      type="file" 
      style="display: none" 
      @change="handleFileSelect"
      :accept="acceptedFileTypes"
    />
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'FileUpload',
  setup() {
    const router = useRouter()
    
    // 响应式数据
    const selectedFile = ref(null)
    const isUploading = ref(false)
    const isPaused = ref(false)
    const uploadProgress = ref(0)
    const isDragOver = ref(false)
    const fileInput = ref(null)
    
    // 上传设置
    const uploadFolder = ref('')
    const compressionLevel = ref('none')
    const afterUpload = ref('stay')
    
    // 最近文件数据
    const recentFiles = ref([
      {
        id: 1,
        name: 'project-report.pdf',
        size: 2048576,
        uploadDate: new Date('2024-01-15')
      },
      {
        id: 2,
        name: 'presentation.pptx',
        size: 5242880,
        uploadDate: new Date('2024-01-14')
      },
      {
        id: 3,
        name: 'data-analysis.xlsx',
        size: 1048576,
        uploadDate: new Date('2024-01-13')
      }
    ])
    
    // 计算属性
    const acceptedFileTypes = computed(() => {
      return '.fastq,.fasta,.vcf,.bam,.sam,.bed,.gtf,.gff,.pdf,.doc,.docx,.ppt,.pptx,.rtf,.csv,.tsv,.xls,.xlsx,.json,.xml,.yaml,.sql,.py,.ipynb,.r,.rmd,.js,.html,.css,.java,.cpp,.c,.sh,.pl,.php,.rb,.go,.rs,.swift,.kt,.scala,.txt,.md,.log,.conf,.ini,.cfg,.jpg,.jpeg,.png,.gif,.bmp,.tiff,.svg,.webp,.ico,.mp3,.wav,.flac,.aac,.ogg,.m4a,.mp4,.avi,.mov,.wmv,.flv,.mkv,.webm,.m4v,.zip,.rar,.7z,.tar,.gz,.bz2,.xz'
    })
    
    // 方法
    const triggerFileInput = () => {
      fileInput.value?.click()
    }
    
    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        selectedFile.value = file
        uploadProgress.value = 0
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
        selectedFile.value = files[0]
        uploadProgress.value = 0
      }
    }
    
    const startUpload = () => {
      if (!selectedFile.value) return
      
      isUploading.value = true
      isPaused.value = false
      
      // 模拟上传进度
      const interval = setInterval(() => {
        if (!isPaused.value) {
          uploadProgress.value += Math.random() * 10
          if (uploadProgress.value >= 100) {
            uploadProgress.value = 100
            isUploading.value = false
            clearInterval(interval)
            
            // 添加到最近文件列表
            recentFiles.value.unshift({
              id: Date.now(),
              name: selectedFile.value.name,
              size: selectedFile.value.size,
              uploadDate: new Date()
            })
            
            // 根据设置执行后续操作
            if (afterUpload.value === 'redirect') {
              router.push('/files')
            }
          }
        }
      }, 200)
    }
    
    const pauseUpload = () => {
      isPaused.value = true
    }
    
    const resumeUpload = () => {
      isPaused.value = false
    }
    
    const cancelUpload = () => {
      isUploading.value = false
      isPaused.value = false
      uploadProgress.value = 0
    }
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    const formatDate = (date) => {
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }
    
    const viewFile = (file) => {
      // 查看文件详情
      console.log('查看文件:', file)
    }
    
    const downloadFile = async (file) => {
      try {
        const result = await filesStore.downloadFile(
          file.id, 
          file.original_filename || `file_${file.id}`, 
          file.file_size
        )
        // 错误处理已在store中完成，这里不需要额外处理
        if (result.success) {
          // 可以在这里添加下载成功的处理逻辑
          console.log('下载开始:', file.original_filename)
        }
      } catch (error) {
        console.error('下载失败:', error)
        filesStore.showErrorNotification(`下载失败: ${error.message}`)
      }
    }
    
    return {
      selectedFile,
      isUploading,
      isPaused,
      uploadProgress,
      isDragOver,
      fileInput,
      uploadFolder,
      compressionLevel,
      afterUpload,
      recentFiles,
      acceptedFileTypes,
      triggerFileInput,
      handleFileSelect,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      startUpload,
      pauseUpload,
      resumeUpload,
      cancelUpload,
      formatFileSize,
      formatDate,
      viewFile,
      downloadFile
    }
  }
}
</script>

<style scoped>
/* 主容器样式 */
.file-upload {
  min-height: 100vh;
  padding: 40px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-container {
  max-width: 900px;
  width: 100%;
  background: var(--waves-card-bg);
  border-radius: var(--waves-border-radius-lg);
  box-shadow: var(--waves-shadow-xl);
  border: var(--waves-border-subtle);
  backdrop-filter: var(--waves-backdrop-filter);
  overflow: hidden;
}

.upload-header {
  padding: 40px 48px 32px;
  text-align: center;
  background: var(--waves-gradient-subtle);
  border-bottom: var(--waves-border-subtle);
}

.upload-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 12px;
  background: var(--waves-gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.upload-subtitle {
  font-size: 1.1rem;
  margin: 0;
  opacity: 0.9;
}

.upload-content {
  padding: 48px;
}

/* 上传区域样式 */
.upload-area {
  border: 2px dashed var(--waves-border-color);
  border-radius: var(--waves-border-radius-lg);
  padding: 48px 32px;
  text-align: center;
  background: var(--waves-card-secondary-bg);
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.upload-area:hover {
  border-color: var(--waves-primary);
  background: var(--waves-card-hover-bg);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-lg);
}

.upload-area.waves-upload-active {
  border-color: var(--waves-primary);
  background: var(--waves-primary-bg);
  transform: scale(1.02);
  box-shadow: var(--waves-shadow-xl);
}

.upload-area.has-file {
  border-color: var(--waves-success);
  background: var(--waves-success-bg);
}

/* 上传图标和内容 */
.waves-upload-icon {
  color: var(--waves-primary);
  margin-bottom: 24px;
  opacity: 0.8;
  transition: all 0.3s ease;
}

.upload-area:hover .waves-upload-icon {
  opacity: 1;
  transform: scale(1.1);
}

.upload-zone-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.upload-zone-subtitle {
  font-size: 1rem;
  margin-bottom: 32px;
  line-height: 1.6;
}

/* 功能标签 */
.upload-features {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.feature-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--waves-card-bg);
  border-radius: var(--waves-border-radius);
  border: var(--waves-border-subtle);
  font-size: 0.9rem;
  color: var(--waves-text-light);
  transition: all 0.3s ease;
}

.feature-tag:hover {
  background: var(--waves-primary-bg);
  border-color: var(--waves-primary);
  color: var(--waves-primary);
}

.feature-icon {
  font-size: 1rem;
}

/* 文件预览样式 */
.waves-file-preview {
  background: var(--waves-card-secondary-bg);
  border-radius: var(--waves-border-radius-lg);
  padding: 32px;
  border: var(--waves-border-subtle);
}

.file-preview-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: var(--waves-border-subtle);
}

.waves-file-icon {
  color: var(--waves-primary);
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  text-align: left;
}

.file-name {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 8px;
  word-break: break-all;
  line-height: 1.4;
}

.file-size {
  font-size: 1rem;
  margin-bottom: 12px;
}

.file-status {
  display: flex;
  gap: 8px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: var(--waves-border-radius);
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-badge.ready {
  background: var(--waves-success-bg);
  color: var(--waves-success);
  border: 1px solid var(--waves-success);
}

/* 按钮样式 */
.upload-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.waves-btn {
  padding: 12px 24px;
  border-radius: var(--waves-border-radius);
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  min-width: 120px;
  justify-content: center;
  box-shadow: var(--waves-shadow-sm);
}

.btn-primary.waves-btn {
  background: var(--waves-primary);
  color: white;
}

.btn-primary.waves-btn:hover:not(:disabled) {
  background: var(--waves-primary-hover);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-lg);
}

.btn-secondary.waves-btn {
  background: var(--waves-secondary);
  color: white;
}

.btn-secondary.waves-btn:hover:not(:disabled) {
  background: var(--waves-secondary-hover);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-lg);
}

.btn-success.waves-btn {
  background: var(--waves-success);
  color: white;
}

.btn-success.waves-btn:hover:not(:disabled) {
  background: var(--waves-success-hover);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-lg);
}

.btn-warning.waves-btn {
  background: var(--waves-warning);
  color: white;
}

.btn-warning.waves-btn:hover:not(:disabled) {
  background: var(--waves-warning-hover);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-lg);
}

.btn-danger.waves-btn {
  background: var(--waves-danger);
  color: white;
}

.btn-danger.waves-btn:hover:not(:disabled) {
  background: var(--waves-danger-hover);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-lg);
}

.waves-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

/* 加载动画 */
.waves-loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 简约进度条样式 */
.simple-progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.simple-progress-bar .progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #06b6d4);
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

.simple-progress-bar .progress-text {
  position: absolute;
  top: 8px;
  right: 20px;
  font-size: 12px;
  font-weight: 600;
  color: var(--waves-primary);
  background: rgba(255, 255, 255, 0.9);
  padding: 4px 8px;
  border-radius: 4px;
  backdrop-filter: blur(10px);
}

/* 文件进度条样式 */
.file-progress-bar {
  position: relative;
  width: 100%;
  height: 6px;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 3px;
  margin-bottom: 12px;
  overflow: hidden;
  border: 1px solid rgba(59, 130, 246, 0.2);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1);
}

.file-progress-bar .progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #06b6d4);
  transition: width 0.3s ease;
  border-radius: 3px;
  box-shadow: 0 0 6px rgba(59, 130, 246, 0.4);
}

.file-progress-bar .progress-text {
  position: absolute;
  top: -24px;
  right: 0;
  font-size: 11px;
  font-weight: 600;
  color: var(--waves-primary);
  background: rgba(255, 255, 255, 0.95);
  padding: 2px 6px;
  border-radius: 3px;
  border: 1px solid rgba(59, 130, 246, 0.2);
}

/* 设置区域样式 */
.waves-settings-section {
  margin-top: 32px;
  padding: 32px;
  background: var(--waves-card-secondary-bg);
  border-radius: var(--waves-border-radius-lg);
  border: var(--waves-border-subtle);
}

.settings-title {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.settings-icon {
  color: var(--waves-primary);
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 24px;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setting-label {
  font-weight: 600;
  color: var(--waves-text-primary);
  font-size: 0.95rem;
}

.setting-input {
  padding: 12px 16px;
  border: var(--waves-border-subtle);
  border-radius: var(--waves-border-radius);
  background: var(--waves-card-bg);
  color: var(--waves-text-primary);
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.setting-input:focus {
  outline: none;
  border-color: var(--waves-primary);
  box-shadow: 0 0 0 3px var(--waves-primary-bg);
}

/* 最近文件区域样式 */
.waves-recent-section {
  margin-top: 32px;
  padding: 32px;
  background: var(--waves-card-secondary-bg);
  border-radius: var(--waves-border-radius-lg);
  border: var(--waves-border-subtle);
}

.recent-title {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.recent-icon {
  color: var(--waves-primary);
}

.recent-files {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.recent-file-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--waves-card-bg);
  border-radius: var(--waves-border-radius);
  border: var(--waves-border-subtle);
  transition: all 0.3s ease;
  cursor: pointer;
}

.recent-file-item:hover {
  background: var(--waves-card-hover-bg);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-md);
}

.recent-file-icon {
  color: var(--waves-primary);
  flex-shrink: 0;
}

.recent-file-info {
  flex: 1;
  min-width: 0;
}

.recent-file-name {
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--waves-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recent-file-meta {
  display: flex;
  gap: 16px;
  font-size: 0.85rem;
  color: var(--waves-text-light);
}

.recent-file-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  padding: 8px;
  border: none;
  background: transparent;
  color: var(--waves-text-light);
  border-radius: var(--waves-border-radius);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: var(--waves-primary-bg);
  color: var(--waves-primary);
  transform: scale(1.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .file-upload {
    padding: 20px 16px;
  }
  
  .upload-container {
    margin: 0;
    border-radius: var(--waves-border-radius);
  }
  
  .upload-header {
    padding: 32px 24px 24px;
  }
  
  .upload-title {
    font-size: 2rem;
  }
  
  .upload-content {
    padding: 32px 24px;
  }
  
  .upload-area {
    padding: 32px 20px;
  }
  
  .upload-features {
    flex-direction: column;
    align-items: center;
  }
  
  .upload-actions {
    flex-direction: column;
  }
  
  .waves-btn {
    width: 100%;
  }
  
  .settings-grid {
    grid-template-columns: 1fr;
  }
  
  .recent-file-item {
    padding: 16px;
  }
  
  .recent-file-meta {
    flex-direction: column;
    gap: 4px;
  }
}

@media (max-width: 480px) {
  .upload-title {
    font-size: 1.8rem;
  }
  
  .upload-subtitle {
    font-size: 1rem;
  }
  
  .upload-zone-title {
    font-size: 1.3rem;
  }
  
  .upload-zone-subtitle {
    font-size: 0.9rem;
  }
  
  .file-preview-header {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .file-info {
    text-align: center;
  }
}
</style>
