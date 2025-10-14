<template>
  <div class="file-list">
    <div class="card">
      <div class="card-header" :style="{ display: 'flex', justifyContent: files.length === 0 ? 'center' : 'space-between', alignItems: 'center' }">
        <h2 class="card-title text-white">我的文件</h2>
        <router-link v-if="files.length > 0" to="/upload" class="btn btn-primary">上传新文件</router-link>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-error">
          {{ error }}
        </div>
        
        <div v-if="successMessage" class="alert alert-success">
          {{ successMessage }}
        </div>
        
        <div v-if="isLoading" style="text-align: center; padding: 40px;">
          <div class="loading"></div>
          <p style="margin-top: 10px; color: #605e5c;">加载文件列表中...</p>
        </div>
        
        <div v-else-if="files.length === 0" style="text-align: center; padding: 40px;">
          <p class="lead" style="text-align: center;">您还没有上传任何文件</p>
          <router-link to="/upload" class="btn btn-primary">立即上传</router-link>
        </div>
        
        <div v-else>
          <!-- 文件统计 -->
          <div class="stats-grid">
            <div class="stat-card stat-total">
              <div class="stat-number">{{ files.length }}</div>
              <div class="stat-label">总文件数</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">{{ formatFileSize(totalSize) }}</div>
              <div class="stat-label">总大小</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">{{ files.filter(f => f.upload_method === 'web').length }}</div>
              <div class="stat-label">网页上传</div>
            </div>
            <div class="stat-card">
              <div class="stat-number">{{ files.filter(f => f.upload_method === 'api').length }}</div>
              <div class="stat-label">API上传</div>
            </div>
          </div>
          
          <div class="table-responsive">
            <table class="table">
              <thead>
                <tr>
                  <th>文件名</th>
                  <th>大小</th>
                  <th>上传方式</th>
                  <th>上传时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="file in filesSorted" :key="file.id">
                  <td>
                    <div style="display: flex; align-items: center;">
                      <span class="file-icon">{{ getFileIcon(file) }}</span>
                      <span style="margin-left: 8px;">{{ getFileDisplayName(file) }}</span>
                    </div>
                  </td>
                  <td>{{ formatFileSize(file.file_size) }}</td>
                  <td>
                    <span class="upload-method-plain">{{ file.upload_method }}</span>
                  </td>
                  <td>{{ formatDate(file.uploaded_at) }}</td>
                  <td>
                    <div style="display: flex; gap: 5px;">
                      <button
                        @click="downloadFile(file)"
                        class="btn btn-primary"
                        :disabled="isDownloading(file.id)"
                      >
                        <span v-if="isDownloading(file.id) && !downloadPaused(file.id)" class="loading" style="width: 12px; height: 12px;"></span>
                        {{ isDownloading(file.id) ? (downloadPercent(file.id) + '%') : '下载' }}
                      </button>
                      <button
                        v-if="isDownloading(file.id) && !downloadPaused(file.id)"
                        @click="pauseDownload(file.id)"
                        class="btn btn-secondary"
                        style="padding: 4px 8px; font-size: 12px;"
                      >
                        暂停
                      </button>
                      <button
                        v-if="isDownloading(file.id) && downloadPaused(file.id)"
                        @click="resumeDownload(file.id, getFileDisplayName(file), file.file_size)"
                        class="btn btn-secondary"
                        style="padding: 4px 8px; font-size: 12px;"
                      >
                        继续
                      </button>
                      <button
                        v-if="isDownloading(file.id)"
                        @click.stop="cancelDownload(file.id)"
                        class="btn btn-danger"
                        style="padding: 4px 8px; font-size: 12px;"
                      >
                        取消
                      </button>
                      <button
                        v-if="!isDownloading(file.id) && !downloadPaused(file.id)"
                        @click="confirmDelete(file)"
                        class="btn btn-danger"
                        style="padding: 4px 8px; font-size: 12px;"
                        :disabled="deletingFiles.includes(file.id)"
                      >
                        <span v-if="deletingFiles.includes(file.id)" class="loading" style="width: 12px; height: 12px;"></span>
                        {{ deletingFiles.includes(file.id) ? '删除中' : '删除' }}
                      </button>
                    </div>
                    <div v-if="isDownloading(file.id)" class="download-progress">
                      <div class="progress">
                        <div class="progress-bar" :style="{ width: downloadPercent(file.id) + '%' }"></div>
                      </div>
                      <div class="progress-text">下载进度: {{ downloadPercent(file.id) }}%</div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 删除确认对话框 -->
    <div v-if="showDeleteDialog" class="modal-overlay" @click="cancelDelete">
      <div class="modal-dialog" @click.stop>
        <div class="modal-header">
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p>确定要删除文件 "{{ fileToDelete ? getFileDisplayName(fileToDelete) : '' }}" 吗？此操作不可撤销。</p>
        </div>
        <div class="modal-footer">
          <button @click="cancelDelete" class="btn btn-secondary">取消</button>
          <button @click="deleteFile" class="btn btn-danger">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useFilesStore } from '../stores/files'

export default {
  name: 'FileList',
  setup() {
    const filesStore = useFilesStore()
    
    const successMessage = ref('')
    const showDeleteDialog = ref(false)
    const fileToDelete = ref(null)
    const downloadingFiles = ref([])
    const deletingFiles = ref([])
    
    const files = computed(() => filesStore.files)
    const filesSorted = computed(() => {
      // 按上传时间倒序
      return [...files.value].sort((a, b) => {
        const at = a.uploaded_at ? new Date(a.uploaded_at).getTime() : 0
        const bt = b.uploaded_at ? new Date(b.uploaded_at).getTime() : 0
        return bt - at
      })
    })
    const isLoading = computed(() => filesStore.isLoading)
    const error = computed(() => filesStore.error)
    const totalSize = computed(() => {
      return files.value.reduce((total, file) => total + (file.file_size || 0), 0)
    })
    
    const getFileDisplayName = (file) => {
      // 优先使用 original_filename，其次从 file 字段路径中提取
      if (file?.original_filename) return file.original_filename
      const filePath = file?.file
      return filePath ? filePath.split('/').pop() : '未知文件'
    }
    
    const getFileIcon = (file) => {
      const fileName = (file?.original_filename || file?.file || '').split('/').pop().toLowerCase()
      if (!fileName) return '📄'
      const ext = fileName.split('.').pop()
      
      const iconMap = {
        'pdf': '📕',
        'doc': '📘',
        'docx': '📘',
        'txt': '📄',
        'md': '📝',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️',
        'mp4': '🎬',
        'avi': '🎬',
        'mp3': '🎵',
        'wav': '🎵',
        'zip': '📦',
        'rar': '📦',
        'xlsx': '📊',
        'xls': '📊',
        'ppt': '📋',
        'pptx': '📋'
      }
      
      return iconMap[ext] || '📄'
    }
    
    const formatFileSize = (bytes) => {
      if (!bytes || bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return '未知'
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    const downloadFile = async (file) => {
      let result
      try {
        result = await filesStore.downloadFile(file.id, getFileDisplayName(file), file.file_size)
        if (result.success) {
          showMessage(result.message, 'success')
        } else {
          showMessage(result.error, 'error')
        }
      } finally {
        // 状态由 store 控制：downloadActive / downloadPaused
      }
    }

    const downloadPercent = (fileId) => {
      const p = filesStore.downloadProgress[fileId]
      return typeof p === 'number' ? p : 0
    }

    const pauseDownload = (fileId) => {
      filesStore.pauseDownload(fileId)
    }

    const cancelDownload = async (fileId) => {
      await filesStore.cancelDownload(fileId)
    }
    
    const downloadPaused = (fileId) => {
      return !!filesStore.downloadPaused?.[fileId]
    }
    
    const resumeDownload = (fileId, filename, size) => {
      filesStore.resumeDownload(fileId, filename, size)
    }

    const isDownloading = (fileId) => {
      return !!filesStore.downloadActive?.[fileId]
    }
    
    const confirmDelete = (file) => {
      fileToDelete.value = file
      showDeleteDialog.value = true
    }
    
    const cancelDelete = () => {
      showDeleteDialog.value = false
      fileToDelete.value = null
    }
    
    const deleteFile = async () => {
      if (!fileToDelete.value) return
      
      deletingFiles.value.push(fileToDelete.value.id)
      try {
        const result = await filesStore.deleteFile(fileToDelete.value.id)
        if (result.success) {
          showMessage(result.message, 'success')
        } else {
          showMessage(result.error, 'error')
        }
      } finally {
        deletingFiles.value = deletingFiles.value.filter(id => id !== fileToDelete.value.id)
        showDeleteDialog.value = false
        fileToDelete.value = null
      }
    }
    
    const showMessage = (message, type) => {
      if (type === 'success') {
        successMessage.value = message
        setTimeout(() => {
          successMessage.value = ''
        }, 3000)
      }
    }
    
    onMounted(() => {
      filesStore.fetchFiles()
    })
    
    return {
      files,
      filesSorted,
      isLoading,
      error,
      successMessage,
      totalSize,
      showDeleteDialog,
      fileToDelete,
      downloadingFiles,
      deletingFiles,
      getFileDisplayName,
      getFileIcon,
      formatFileSize,
      formatDate,
      downloadFile,
      pauseDownload,
      cancelDownload,
      downloadPaused,
      resumeDownload,
      confirmDelete,
      cancelDelete,
      deleteFile,
      downloadPercent,
      isDownloading
    }
  }
}
</script>

<style scoped>
.file-list {
  /* 上移页面整体位置，使与其他页面一致 */
  margin-top: -16px;
}

.file-list .card {
  /* 允许内容溢出显示，避免按钮悬停位移被裁剪 */
  overflow: visible;
}

.file-icon {
  font-size: 16px;
}

.badge {
  background-color: var(--brand-blue);
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

/* 上传方式改为纯文本展示：黑色、与表格文字大小一致、无框 */
.upload-method-plain {
  color: #000000;
  font-size: 14px;
  font-weight: normal;
  padding: 0;
  background: none;
  border: none;
  border-radius: 0;
}

.table-responsive {
  overflow-x: auto;
  border-radius: 20px;
  overflow: hidden; /* 裁剪子元素以呈现圆角 */
}

.table {
  border-radius: 20px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-dialog {
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  max-width: 400px;
  width: 90%;
}

.modal-header {
  padding: 20px 20px 0;
}

.modal-header h3 {
  margin: 0;
  color: #323130;
}

.modal-body {
  padding: 20px;
  color: #605e5c;
}

.modal-footer {
  padding: 0 20px 20px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  background-color: #121212;
  border-radius: 20px;
  padding: 20px;
  text-align: center;
  border: 1px solid #383838;
}

/* 总文件数卡片单独占第一行，铺满整行 */
.stat-card.stat-total {
  grid-column: 1 / -1;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 12px;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
/* 文件名卡片内去除所有分割线 */
.table,
.table th,
.table td,
.table thead tr,
.table tbody tr {
  border: none !important;
}
.table thead th,
.table tbody td {
  border-bottom: none !important;
}
.table tbody tr {
  box-shadow: none !important;
}
.download-progress {
  margin-top: 8px;
}
.download-progress .progress {
  width: 180px;
  height: 6px;
  background-color: #eee;
  border-radius: 4px;
}
.download-progress .progress-bar {
  height: 6px;
  background-color: var(--brand-blue);
  border-radius: 4px;
  transition: width 0.2s ease;
}
.download-progress .progress-text {
  font-size: 12px;
  color: #605e5c;
  margin-top: 4px;
}
</style>