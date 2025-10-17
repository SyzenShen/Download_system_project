<template>
  <div class="navigation-bar">
    <!-- 左侧：面包屑导航 -->
    <div class="breadcrumb-section">
      <!-- 返回上一级按钮 -->
      <button 
        v-if="currentFolderId !== null"
        class="back-button"
        @click="navigateUp"
        title="返回上一级目录"
      >
        ← 返回
      </button>
      
      <div class="breadcrumb">
        <span 
          class="breadcrumb-item"
          :class="{ active: currentFolderId === null }"
          @click="navigateToRoot"
        >
          <span class="breadcrumb-icon">🏠</span>
          全部文件
        </span>
        
        <template v-for="(folder, index) in breadcrumbPath" :key="folder.id">
          <span class="breadcrumb-separator">></span>
          <span 
            class="breadcrumb-item"
            :class="{ active: index === breadcrumbPath.length - 1 }"
            @click="navigateToFolder(folder.id)"
          >
            {{ folder.name }}
          </span>
        </template>
      </div>
    </div>
    
    <!-- 右侧：操作工具栏 -->
    <div class="toolbar-section">
      <!-- 视图切换 -->
      <div class="view-toggle">
        <button 
          class="view-btn"
          :class="{ active: viewMode === 'list' }"
          @click="setViewMode('list')"
          title="列表视图"
        >
          ☰
        </button>
        <button 
          class="view-btn"
          :class="{ active: viewMode === 'grid' }"
          @click="setViewMode('grid')"
          title="网格视图"
        >
          ⊞
        </button>
      </div>
      
      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button 
          class="action-btn"
          @click="showUploadDialog"
        >
          📤 上传文件
        </button>
        
        <button 
          class="action-btn"
          @click="showNewFolderDialog"
        >
          📁 新建文件夹
        </button>
        
        <button 
          class="action-btn"
          @click="refreshFiles"
          :disabled="isLoading"
        >
          🔄 刷新
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useFilesStore } from '../stores/files'

const filesStore = useFilesStore()

// 计算属性
const currentFolderId = computed(() => filesStore.currentFolderId)
const viewMode = computed(() => filesStore.viewMode)
const isLoading = computed(() => filesStore.isLoading)
const breadcrumbPath = computed(() => filesStore.breadcrumb || [])

// 方法
const navigateToRoot = () => {
  filesStore.navigateToFolder(null)
}

const navigateToFolder = (folderId) => {
  filesStore.navigateToFolder(folderId)
}

const navigateUp = () => {
  filesStore.navigateUp()
}

const setViewMode = (mode) => {
  filesStore.setViewMode(mode)
}

const showUploadDialog = () => {
  console.log('点击上传按钮，当前状态:', filesStore.showUploadDialog)
  filesStore.toggleUploadDialog()
  console.log('切换后状态:', filesStore.showUploadDialog)
}

const showNewFolderDialog = () => {
  console.log('点击新建文件夹按钮，当前状态:', filesStore.showNewFolderDialog)
  filesStore.toggleNewFolderDialog()
  console.log('切换后状态:', filesStore.showNewFolderDialog)
}

const refreshFiles = () => {
  filesStore.fetchFiles(currentFolderId.value)
}
</script>

<style scoped>
.navigation-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e9ecef;
  min-height: 60px;
}

.breadcrumb-section {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-button {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #666;
  white-space: nowrap;
}

.back-button:hover {
  background-color: #f8f9fa;
  border-color: #bbb;
  color: #333;
}

.breadcrumb {
  display: flex;
  align-items: center;
  font-size: 14px;
  overflow-x: auto;
  white-space: nowrap;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  color: #666;
}

.breadcrumb-item:hover {
  background-color: #f8f9fa;
  color: #333;
}

.breadcrumb-item.active {
  color: #007bff;
  font-weight: 500;
}

.breadcrumb-icon {
  margin-right: 4px;
  font-size: 16px;
}

.breadcrumb-separator {
  margin: 0 8px;
  color: #ccc;
  font-size: 12px;
}

.toolbar-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.view-toggle {
  display: flex;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.view-btn {
  padding: 8px 12px;
  border: none;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
}

.view-btn:hover {
  background-color: #f8f9fa;
}

.view-btn.active {
  background-color: #007bff;
  color: white;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  white-space: nowrap;
}

.action-btn:hover {
  background-color: #f8f9fa;
  border-color: #bbb;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn.primary {
  background-color: #007bff;
  color: white;
  border-color: #007bff;
}

.action-btn.primary:hover {
  background-color: #0056b3;
  border-color: #0056b3;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navigation-bar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .toolbar-section {
    justify-content: space-between;
  }
  
  .action-buttons {
    flex-wrap: wrap;
  }
}
</style>