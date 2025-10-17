<template>
  <div class="file-display">
    <!-- 列表视图 -->
    <div v-if="viewMode === 'list'" class="list-view">
      <div class="list-header">
        <div class="header-cell name-cell">名称</div>
        <div class="header-cell size-cell">大小</div>
        <div class="header-cell date-cell">修改时间</div>
        <div class="header-cell action-cell">操作</div>
      </div>
      
      <div class="list-content">
        <!-- 文件夹 -->
        <div 
          v-for="folder in folders"
          :key="`folder-${folder.id}`"
          class="list-item folder-item"
          @click="navigateToFolder(folder.id)"
        >
          <div class="item-cell name-cell">
            <span class="item-icon">📁</span>
            <span class="item-name">{{ folder.name }}</span>
          </div>
          <div class="item-cell size-cell">-</div>
          <div class="item-cell date-cell">{{ formatDate(folder.created_at) }}</div>
          <div class="item-cell action-cell">
            <button 
              class="action-button"
              @click.stop="downloadFolder(folder.id)"
              title="下载文件夹"
            >
              📦
            </button>
            <button 
              class="action-button"
              @click.stop="deleteFolder(folder.id)"
              title="删除文件夹"
            >
              🗑️
            </button>
          </div>
        </div>
        
        <!-- 文件 -->
        <div 
          v-for="file in files"
          :key="`file-${file.id}`"
          class="list-item file-item"
        >
          <div class="item-cell name-cell">
            <span class="item-icon">{{ getFileIcon(file.original_filename) }}</span>
            <span class="item-name">{{ file.original_filename }}</span>
          </div>
          <div class="item-cell size-cell">{{ formatFileSize(file.file_size) }}</div>
          <div class="item-cell date-cell">{{ formatDate(file.upload_time) }}</div>
          <div class="item-cell action-cell">
            <button 
              class="action-button"
              @click="downloadFile(file)"
              title="下载文件"
            >
              📥
            </button>
            <button 
              class="action-button"
              @click="deleteFile(file.id)"
              title="删除文件"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 网格视图 -->
    <div v-else class="grid-view">
      <div class="grid-content">
        <!-- 文件夹 -->
        <div 
          v-for="folder in folders"
          :key="`folder-${folder.id}`"
          class="grid-item folder-item"
          @click="navigateToFolder(folder.id)"
        >
          <div class="item-icon-large">📁</div>
          <div class="item-name">{{ folder.name }}</div>
          <div class="item-actions">
            <button 
              class="action-button"
              @click.stop="downloadFolder(folder.id)"
              title="下载文件夹"
            >
              📦
            </button>
            <button 
              class="action-button"
              @click.stop="deleteFolder(folder.id)"
              title="删除文件夹"
            >
              🗑️
            </button>
          </div>
        </div>
        
        <!-- 文件 -->
        <div 
          v-for="file in files"
          :key="`file-${file.id}`"
          class="grid-item file-item"
        >
          <div class="item-icon-large">{{ getFileIcon(file.original_filename) }}</div>
          <div class="item-name" :title="file.original_filename">{{ file.original_filename }}</div>
          <div class="item-size">{{ formatFileSize(file.file_size) }}</div>
          <div class="item-actions">
            <button 
              class="action-button"
              @click="downloadFile(file)"
              title="下载文件"
            >
              📥
            </button>
            <button 
              class="action-button"
              @click="deleteFile(file.id)"
              title="删除文件"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-if="isEmpty" class="empty-state">
      <div class="empty-icon">📂</div>
      <div class="empty-text">此文件夹为空</div>
      <div class="empty-hint">您可以上传文件或创建新文件夹</div>
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

const downloadFile = (file) => {
  // 创建下载链接
  const link = document.createElement('a')
  link.href = file.file_path
  link.download = file.original_filename
  link.click()
}

const downloadFolder = async (folderId) => {
  try {
    // 创建下载链接
    const link = document.createElement('a')
    link.href = `http://localhost:8001/file_download/download/folder/${folderId}/`
    link.download = '' // 让浏览器自动处理文件名
    link.click()
  } catch (error) {
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

const getFileIcon = (filename) => {
  if (!filename) return '📄'
  const ext = filename.split('.').pop()?.toLowerCase()
  
  const iconMap = {
    // 图片
    'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'bmp': '🖼️', 'svg': '🖼️',
    // 文档
    'pdf': '📕', 'doc': '📘', 'docx': '📘', 'txt': '📄', 'rtf': '📄',
    // 表格
    'xls': '📗', 'xlsx': '📗', 'csv': '📗',
    // 演示文稿
    'ppt': '📙', 'pptx': '📙',
    // 压缩文件
    'zip': '🗜️', 'rar': '🗜️', '7z': '🗜️', 'tar': '🗜️', 'gz': '🗜️',
    // 音频
    'mp3': '🎵', 'wav': '🎵', 'flac': '🎵', 'aac': '🎵',
    // 视频
    'mp4': '🎬', 'avi': '🎬', 'mkv': '🎬', 'mov': '🎬', 'wmv': '🎬',
    // 代码
    'js': '📜', 'html': '📜', 'css': '📜', 'py': '📜', 'java': '📜', 'cpp': '📜'
  }
  
  return iconMap[ext] || '📄'
}
</script>

<style scoped>
.file-display {
  flex: 1;
  height: 100%;
  overflow: hidden;
}

/* 列表视图样式 */
.list-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  padding: 12px 16px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  font-weight: 600;
  font-size: 14px;
  color: #666;
}

.list-content {
  flex: 1;
  overflow-y: auto;
}

.list-item {
  display: flex;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f1f1;
  transition: background-color 0.2s;
  cursor: pointer;
}

.list-item:hover {
  background-color: #f8f9fa;
}

.folder-item {
  font-weight: 500;
}

.header-cell,
.item-cell {
  display: flex;
  align-items: center;
}

.name-cell {
  flex: 1;
  min-width: 200px;
}

.size-cell {
  width: 100px;
  justify-content: flex-end;
}

.date-cell {
  width: 150px;
  justify-content: center;
}

.action-cell {
  width: 100px;
  justify-content: center;
  gap: 8px;
}

.item-icon {
  margin-right: 8px;
  font-size: 16px;
}

.item-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 网格视图样式 */
.grid-view {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}

.grid-content {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 16px;
}

.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  background: #fff;
  transition: all 0.2s;
  cursor: pointer;
  position: relative;
}

.grid-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.1);
}

.item-icon-large {
  font-size: 48px;
  margin-bottom: 8px;
}

.grid-item .item-name {
  font-size: 12px;
  text-align: center;
  word-break: break-all;
  line-height: 1.3;
  max-height: 2.6em;
  overflow: hidden;
  margin-bottom: 4px;
}

.item-size {
  font-size: 11px;
  color: #666;
  margin-bottom: 8px;
}

.item-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.grid-item:hover .item-actions {
  opacity: 1;
}

/* 操作按钮样式 */
.action-button {
  padding: 4px 8px;
  border: none;
  background: #f8f9fa;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 14px;
}

.action-button:hover {
  background-color: #e9ecef;
}

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 14px;
  opacity: 0.7;
}

/* 滚动条样式 */
.list-content::-webkit-scrollbar,
.grid-view::-webkit-scrollbar {
  width: 6px;
}

.list-content::-webkit-scrollbar-track,
.grid-view::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.list-content::-webkit-scrollbar-thumb,
.grid-view::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.list-content::-webkit-scrollbar-thumb:hover,
.grid-view::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .grid-content {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 12px;
  }
  
  .date-cell {
    display: none;
  }
  
  .size-cell {
    width: 80px;
  }
  
  .action-cell {
    width: 80px;
  }
}
</style>