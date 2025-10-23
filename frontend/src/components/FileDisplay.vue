<template>
  <div class="waves-file-display">
    <!-- 列表视图 -->
    <div v-if="viewMode === 'list'" class="waves-list-view">
      <!-- 表格头部 -->
      <div class="waves-table-header">
        <div class="waves-header-cell waves-name-cell">
          <svg class="waves-header-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6C4.9 2 4.01 2.9 4.01 4L4 20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2ZM18 20H6V4H13V9H18V20Z" fill="currentColor"/>
          </svg>
          名称
        </div>
        <div class="waves-header-cell waves-size-cell">
          <svg class="waves-header-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L13.09 8.26L20 9L13.09 9.74L12 16L10.91 9.74L4 9L10.91 8.26L12 2Z" fill="currentColor"/>
          </svg>
          大小
        </div>
        <div class="waves-header-cell waves-date-cell">
          <svg class="waves-header-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M19 3H18V1H16V3H8V1H6V3H5C3.89 3 3.01 3.9 3.01 5L3 19C3 20.1 3.89 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3ZM19 19H5V8H19V19ZM7 10H12V15H7V10Z" fill="currentColor"/>
          </svg>
          修改时间
        </div>
        <div class="waves-header-cell waves-action-cell">
          <svg class="waves-header-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 8C13.1 8 14 7.1 14 6C14 4.9 13.1 4 12 4C10.9 4 10 4.9 10 6C10 7.1 10.9 8 12 8ZM12 10C10.9 10 10 10.9 10 12C10 13.1 10.9 14 12 14C13.1 14 14 13.1 14 12C14 10.9 13.1 10 12 10ZM12 16C10.9 16 10 16.9 10 18C10 19.1 10.9 20 12 20C13.1 20 14 19.1 14 18C14 16.9 13.1 16 12 16Z" fill="currentColor"/>
          </svg>
          操作
        </div>
      </div>
      
      <!-- 表格内容 -->
      <div class="waves-table-content">
        <!-- 文件夹 -->
        <div 
          v-for="folder in folders"
          :key="`folder-${folder.id}`"
          class="waves-table-row waves-folder-row"
          @click="navigateToFolder(folder.id)"
        >
          <div class="waves-cell waves-name-cell">
            <div class="waves-file-icon waves-folder-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 4H4C2.89 4 2.01 4.89 2.01 6L2 18C2 19.11 2.89 20 4 20H20C21.11 20 22 19.11 22 18V8C22 6.89 21.11 6 20 6H12L10 4Z" fill="currentColor"/>
              </svg>
            </div>
            <div class="waves-file-info">
              <div class="waves-file-name">{{ folder.name }}</div>
              <div class="waves-file-type">文件夹</div>
            </div>
          </div>
          <div class="waves-cell waves-size-cell">
            <span class="waves-size-text">{{ formatFileSize(folder.folder_size) }}</span>
          </div>
          <div class="waves-cell waves-date-cell">
            <span class="waves-date-text">{{ formatDate(folder.created_at) }}</span>
          </div>
          <div class="waves-cell waves-action-cell">
            <div class="waves-action-group">
              <button 
                class="waves-action-btn waves-download-btn"
                @click.stop="downloadFolder(folder.id)"
                title="下载文件夹"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M5 20H19V18H5M19 9H15V3H9V9H5L12 16L19 9Z" fill="currentColor"/>
                </svg>
              </button>
              <button 
                class="waves-action-btn waves-delete-btn"
                @click.stop="deleteFolder(folder.id)"
                title="删除文件夹"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 4H15.5L14.5 3H9.5L8.5 4H5V6H19M6 19C6 20.1 6.9 21 8 21H16C17.1 21 18 20.1 18 19V7H6V19Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        <!-- 文件 -->
        <div 
          v-for="file in files"
          :key="`file-${file.id}`"
          class="waves-table-row waves-file-row"
        >
          <div class="waves-cell waves-name-cell">
            <div class="waves-file-icon waves-document-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C4.9 2 4.01 2.9 4.01 4L4 20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2ZM18 20H6V4H13V9H18V20Z" fill="currentColor"/>
              </svg>
            </div>
            <div class="waves-file-info">
              <div class="waves-file-name">{{ file.original_filename }}</div>
              <div class="waves-file-type">{{ getFileType(file.original_filename) }}</div>
            </div>
          </div>
          <div class="waves-cell waves-size-cell">
            <span class="waves-size-text">{{ formatFileSize(file.file_size) }}</span>
          </div>
          <div class="waves-cell waves-date-cell">
            <span class="waves-date-text">{{ formatDate(file.upload_time) }}</span>
          </div>
          <div class="waves-cell waves-action-cell">
            <div class="waves-action-group">
              <button 
                class="waves-action-btn waves-download-btn"
                @click="downloadFile(file)"
                title="下载文件"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M5 20H19V18H5M19 9H15V3H9V9H5L12 16L19 9Z" fill="currentColor"/>
                </svg>
              </button>
              <button 
                class="waves-action-btn waves-delete-btn"
                @click="deleteFile(file.id)"
                title="删除文件"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 4H15.5L14.5 3H9.5L8.5 4H5V6H19M6 19C6 20.1 6.9 21 8 21H16C17.1 21 18 20.1 18 19V7H6V19Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 网格视图 -->
    <div v-else class="waves-grid-view">
      <div class="waves-grid-content">
        <!-- 文件夹 -->
        <div 
          v-for="folder in folders"
          :key="`folder-${folder.id}`"
          class="waves-grid-item waves-folder-card"
          @click="navigateToFolder(folder.id)"
        >
          <div class="waves-card-header">
            <div class="waves-item-icon waves-folder-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 4H4C2.89 4 2.01 4.89 2.01 6L2 18C2 19.11 2.89 20 4 20H20C21.11 20 22 19.11 22 18V8C22 6.89 21.11 6 20 6H12L10 4Z" fill="currentColor"/>
              </svg>
            </div>
            <div class="waves-item-actions">
              <button 
                class="waves-action-btn waves-download-btn"
                @click.stop="downloadFolder(folder.id)"
                title="下载文件夹"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M5 20H19V18H5M19 9H15V3H9V9H5L12 16L19 9Z" fill="currentColor"/>
                </svg>
              </button>
              <button 
                class="waves-action-btn waves-delete-btn"
                @click.stop="deleteFolder(folder.id)"
                title="删除文件夹"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 4H15.5L14.5 3H9.5L8.5 4H5V6H19M6 19C6 20.1 6.9 21 8 21H16C17.1 21 18 20.1 18 19V7H6V19Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="waves-card-body">
            <div class="waves-item-name">{{ folder.name }}</div>
            <div class="waves-item-meta">
              <span class="waves-item-type">文件夹</span>
              <span class="waves-item-size">{{ formatFileSize(folder.folder_size) }}</span>
              <span class="waves-item-date">{{ formatDate(folder.created_at) }}</span>
            </div>
          </div>
        </div>
        
        <!-- 文件 -->
        <div 
          v-for="file in files"
          :key="`file-${file.id}`"
          class="waves-grid-item waves-file-card"
        >
          <div class="waves-card-header">
            <div class="waves-item-icon waves-document-icon">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C4.9 2 4.01 2.9 4.01 4L4 20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2ZM18 20H6V4H13V9H18V20Z" fill="currentColor"/>
              </svg>
            </div>
            <div class="waves-item-actions">
              <button 
                class="waves-action-btn waves-download-btn"
                @click="downloadFile(file)"
                title="下载文件"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M5 20H19V18H5M19 9H15V3H9V9H5L12 16L19 9Z" fill="currentColor"/>
                </svg>
              </button>
              <button 
                class="waves-action-btn waves-delete-btn"
                @click="deleteFile(file.id)"
                title="删除文件"
              >
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M19 4H15.5L14.5 3H9.5L8.5 4H5V6H19M6 19C6 20.1 6.9 21 8 21H16C17.1 21 18 20.1 18 19V7H6V19Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="waves-card-body">
            <div class="waves-item-name" :title="file.original_filename">{{ file.original_filename }}</div>
            <div class="waves-item-meta">
              <span class="waves-item-type">{{ getFileType(file.original_filename) }}</span>
              <span class="waves-item-size">{{ formatFileSize(file.file_size) }}</span>
              <span class="waves-item-date">{{ formatDate(file.upload_time) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-if="isEmpty" class="waves-empty-state">
      <div class="waves-empty-icon">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M10 4H4C2.89 4 2.01 4.89 2.01 6L2 18C2 19.11 2.89 20 4 20H20C21.11 20 22 19.11 22 18V8C22 6.89 21.11 6 20 6H12L10 4Z" fill="currentColor"/>
        </svg>
      </div>
      <div class="waves-empty-content">
        <h3 class="waves-empty-title">此文件夹为空</h3>
        <p class="waves-empty-description">您可以上传文件或创建新文件夹来开始使用</p>
        <div class="waves-empty-actions">
          <button class="waves-btn waves-btn-primary">
            <svg class="waves-btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M14 2H6C4.9 2 4.01 2.9 4.01 4L4 20C4 21.1 4.89 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2ZM18 20H6V4H13V9H18V20ZM8 15.01L8.01 15H16V17H8V15.01ZM16 11H8V13H16V11ZM12 7V9H16V7H12Z" fill="currentColor"/>
            </svg>
            上传文件
          </button>
          <button class="waves-btn waves-btn-secondary">
            <svg class="waves-btn-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10 4H4C2.89 4 2.01 4.89 2.01 6L2 18C2 19.11 2.89 20 4 20H20C21.11 20 22 19.11 22 18V8C22 6.89 21.11 6 20 6H12L10 4Z" fill="currentColor"/>
            </svg>
            新建文件夹
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useFilesStore } from '../stores/files'

const filesStore = useFilesStore()

// 计算属性
const viewMode = computed(() => filesStore.viewMode)
const folders = computed(() => filesStore.currentFolders)
const files = computed(() => filesStore.currentFiles)
const isEmpty = computed(() => folders.value.length === 0 && files.value.length === 0)

// 方法
const navigateToFolder = (folderId) => {
  filesStore.navigateToFolder(folderId)
}

const deleteFolder = async (folderId) => {
  if (confirm('确定要删除这个文件夹吗？')) {
    const result = await filesStore.deleteFolder(folderId)
    if (!result.success) {
      alert(`删除失败: ${result.error}`)
    }
  }
}

const deleteFile = async (fileId) => {
  if (confirm('确定要删除这个文件吗？')) {
    const result = await filesStore.deleteFile(fileId)
    if (!result.success) {
      alert(`删除失败: ${result.error}`)
    }
  }
}

const downloadFile = async (file) => {
  try {
    // 获取token
    const token = localStorage.getItem('token')
    if (!token) {
      alert('请先登录')
      return
    }

    // 使用fetch进行带认证的下载
    const response = await fetch(`http://localhost:8000/api/files/${file.id}/download/`, {
      method: 'GET',
      headers: {
        'Authorization': `Token ${token}`
      }
    })

    if (!response.ok) {
      throw new Error(`下载失败: ${response.status} ${response.statusText}`)
    }

    // 获取文件blob
    const blob = await response.blob()
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = file.original_filename || `file_${file.id}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 清理URL对象
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载失败:', error)
    alert(`下载失败: ${error.message}`)
  }
}

const downloadFolder = async (folderId) => {
  try {
    // 获取token
    const token = localStorage.getItem('token')
    if (!token) {
      alert('请先登录')
      return
    }

    // 使用fetch进行带认证的文件夹下载
    const response = await fetch(`http://localhost:8000/file_download/download/folder/${folderId}/`, {
      method: 'GET',
      headers: {
        'Authorization': `Token ${token}`
      }
    })

    if (!response.ok) {
      throw new Error(`下载失败: ${response.status} ${response.statusText}`)
    }

    // 获取文件blob
    const blob = await response.blob()
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `folder_${folderId}.zip` // 文件夹下载通常是ZIP格式
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 清理URL对象
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('文件夹下载失败:', error)
    alert(`下载失败: ${error.message}`)
  }
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const getFileType = (filename) => {
  if (!filename) return '未知文件'
  const ext = filename.split('.').pop()?.toLowerCase()
  
  const typeMap = {
    // 图片
    'jpg': '图片文件', 'jpeg': '图片文件', 'png': '图片文件', 'gif': '图片文件', 'bmp': '图片文件', 'svg': '图片文件',
    // 文档
    'pdf': 'PDF文档', 'doc': 'Word文档', 'docx': 'Word文档', 'txt': '文本文件', 'rtf': '富文本文件',
    // 表格
    'xls': 'Excel表格', 'xlsx': 'Excel表格', 'csv': 'CSV文件',
    // 演示文稿
    'ppt': 'PowerPoint', 'pptx': 'PowerPoint',
    // 压缩文件
    'zip': '压缩文件', 'rar': '压缩文件', '7z': '压缩文件', 'tar': '压缩文件', 'gz': '压缩文件',
    // 音频
    'mp3': '音频文件', 'wav': '音频文件', 'flac': '音频文件', 'aac': '音频文件',
    // 视频
    'mp4': '视频文件', 'avi': '视频文件', 'mkv': '视频文件', 'mov': '视频文件', 'wmv': '视频文件',
    // 代码
    'js': 'JavaScript', 'html': 'HTML文件', 'css': 'CSS文件', 'py': 'Python文件', 'java': 'Java文件', 'cpp': 'C++文件'
  }
  
  return typeMap[ext] || '未知文件'
}
</script>

<style scoped>
/* 企业级文件显示组件样式 */
.waves-file-display {
  height: 100%;
  background: var(--waves-surface-primary);
  border-radius: var(--waves-radius-lg);
  overflow: hidden;
  border: 1px solid var(--waves-border-light);
}

/* 列表视图样式 */
.waves-list-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.waves-table-header {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, var(--waves-primary-50), var(--waves-primary-100));
  border-bottom: 2px solid var(--waves-border-light);
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--waves-text-primary);
}

.waves-header-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.waves-header-icon {
  width: 16px;
  height: 16px;
  color: var(--waves-primary-600);
}

.waves-name-cell {
  flex: 1;
  min-width: 250px;
}

.waves-size-cell {
  width: 120px;
  justify-content: center;
}

.waves-date-cell {
  width: 180px;
  justify-content: center;
}

.waves-action-cell {
  width: 120px;
  justify-content: center;
}

.waves-table-content {
  flex: 1;
  overflow-y: auto;
  background: var(--waves-surface-primary);
}

.waves-table-row {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--waves-border-light);
  transition: all 0.3s ease;
  cursor: pointer;
}

.waves-table-row:hover {
  background: var(--waves-surface-secondary);
  transform: translateX(4px);
  border-left: 4px solid var(--waves-primary-500);
}

.waves-folder-row {
  background: linear-gradient(135deg, var(--waves-primary-25), transparent);
}

.waves-cell {
  display: flex;
  align-items: center;
}

.waves-cell.waves-name-cell {
  flex: 1;
  min-width: 250px;
  gap: 1rem;
}

.waves-cell.waves-size-cell,
.waves-cell.waves-date-cell,
.waves-cell.waves-action-cell {
  justify-content: center;
}

.waves-file-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--waves-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.waves-folder-icon {
  background: linear-gradient(135deg, var(--waves-primary-500), var(--waves-primary-600));
  color: white;
}

.waves-document-icon {
  background: linear-gradient(135deg, var(--waves-secondary-500), var(--waves-secondary-600));
  color: white;
}

.waves-file-icon svg {
  width: 20px;
  height: 20px;
}

.waves-file-info {
  flex: 1;
  min-width: 0;
}

.waves-file-name {
  font-weight: 500;
  color: var(--waves-text-primary);
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.waves-file-type {
  font-size: 0.75rem;
  color: var(--waves-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.waves-size-text,
.waves-date-text {
  font-size: 0.875rem;
  color: var(--waves-text-secondary);
}

.waves-action-group {
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.waves-table-row:hover .waves-action-group {
  opacity: 1;
}

.waves-action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--waves-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--waves-surface-secondary);
  color: var(--waves-text-secondary);
}

.waves-action-btn svg {
  width: 16px;
  height: 16px;
}

.waves-download-btn:hover {
  background: #10b981;
  color: white;
  transform: scale(1.1);
}

.waves-delete-btn:hover {
  background: #ef4444;
  color: white;
  transform: scale(1.1);
}

/* 网格视图样式 */
.waves-grid-view {
  height: 100%;
  overflow-y: auto;
  padding: 1.5rem;
  background: var(--waves-surface-primary);
}

.waves-grid-content {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.5rem;
}

.waves-grid-item {
  background: var(--waves-surface-secondary);
  border: 1px solid var(--waves-border-light);
  border-radius: var(--waves-radius-lg);
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: pointer;
}

.waves-grid-item:hover {
  transform: translateY(-4px);
  box-shadow: var(--waves-shadow-lg);
  border-color: var(--waves-primary-300);
}

.waves-folder-card {
  background: linear-gradient(135deg, var(--waves-primary-50), var(--waves-surface-secondary));
}

.waves-card-header {
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--waves-border-light);
}

.waves-grid-item .waves-item-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--waves-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.waves-grid-item .waves-item-icon svg {
  width: 24px;
  height: 24px;
}

.waves-item-actions {
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.waves-grid-item:hover .waves-item-actions {
  opacity: 1;
}

.waves-card-body {
  padding: 1rem;
}

.waves-item-name {
  font-weight: 500;
  color: var(--waves-text-primary);
  margin-bottom: 0.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.waves-item-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.waves-item-type,
.waves-item-size,
.waves-item-date {
  font-size: 0.75rem;
  color: var(--waves-text-secondary);
}

.waves-item-type {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 500;
}

/* 空状态样式 */
.waves-empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.waves-empty-icon {
  width: 120px;
  height: 120px;
  background: var(--waves-surface-secondary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 2rem;
  color: var(--waves-text-secondary);
  opacity: 0.6;
}

.waves-empty-icon svg {
  width: 60px;
  height: 60px;
}

.waves-empty-content {
  max-width: 400px;
}

.waves-empty-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--waves-text-primary);
  margin: 0 0 1rem;
}

.waves-empty-description {
  font-size: 1rem;
  color: var(--waves-text-secondary);
  margin: 0 0 2rem;
  line-height: 1.6;
}

.waves-empty-actions {
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
  background: var(--waves-surface-secondary);
  color: var(--waves-text-primary);
  border: 1px solid var(--waves-border-light);
}

.waves-btn-secondary:hover {
  background: var(--waves-surface-primary);
  border-color: var(--waves-primary-300);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-md);
}

/* 滚动条样式 */
.waves-table-content::-webkit-scrollbar,
.waves-grid-view::-webkit-scrollbar {
  width: 8px;
}

.waves-table-content::-webkit-scrollbar-track,
.waves-grid-view::-webkit-scrollbar-track {
  background: var(--waves-surface-secondary);
  border-radius: var(--waves-radius-sm);
}

.waves-table-content::-webkit-scrollbar-thumb,
.waves-grid-view::-webkit-scrollbar-thumb {
  background: var(--waves-border-light);
  border-radius: var(--waves-radius-sm);
}

.waves-table-content::-webkit-scrollbar-thumb:hover,
.waves-grid-view::-webkit-scrollbar-thumb:hover {
  background: var(--waves-primary-400);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .waves-grid-content {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 1rem;
  }
}

@media (max-width: 768px) {
  .waves-date-cell {
    display: none;
  }
  
  .waves-size-cell {
    width: 100px;
  }
  
  .waves-action-cell {
    width: 100px;
  }
  
  .waves-grid-content {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.75rem;
  }
  
  .waves-grid-view {
    padding: 1rem;
  }
  
  .waves-empty-actions {
    flex-direction: column;
    align-items: center;
  }
}

@media (max-width: 480px) {
  .waves-table-header,
  .waves-table-row {
    padding: 0.75rem 1rem;
  }
  
  .waves-name-cell {
    min-width: 150px;
  }
  
  .waves-size-cell {
    width: 80px;
  }
  
  .waves-action-cell {
    width: 80px;
  }
  
  .waves-grid-content {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }
  
  .waves-card-header,
  .waves-card-body {
    padding: 0.75rem;
  }
}
</style>