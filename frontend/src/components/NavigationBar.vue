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
          class="action-btn search-btn"
          @click="goToSearch"
          title="文件查找"
        >
          查找
        </button>
        
        <button 
          class="action-btn"
          @click="showUploadDialog"
        >
          上传
        </button>
        
        <button 
          class="action-btn"
          @click="showNewFolderDialog"
        >
          新建
        </button>
        
        <button 
          class="action-btn"
          @click="refreshFiles"
          :disabled="isLoading"
        >
          刷新
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useFilesStore } from '../stores/files'

const router = useRouter()
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

const goToSearch = () => {
  router.push('/search')
}
</script>

<style scoped>
.navigation-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
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
  border: 1px solid #8a8886;
  border-radius: var(--waves-radius-sm);
  background: #ffffff;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  color: #323130;
  white-space: nowrap;
  font-weight: 400;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-button:hover {
  background-color: #f3f2f1;
  border-color: #605e5c;
  color: #201f1e;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.back-button:active {
  background-color: #edebe9;
  border-color: #323130;
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
  border-radius: var(--waves-radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  color: #605e5c;
}

.breadcrumb-item:hover {
  background-color: #f3f2f1;
  color: #323130;
}

.breadcrumb-item.active {
  color: rgb(58, 126, 185);
  font-weight: 500;
}

.breadcrumb-icon {
  margin-right: 4px;
  font-size: 16px;
}

.breadcrumb-separator {
  margin: 0 8px;
  color: #666666;
  font-size: 12px;
}

.toolbar-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.view-toggle {
  display: flex;
  border: 1px solid #8a8886;
  border-radius: var(--waves-radius-sm);
  overflow: hidden;
  background: #ffffff;
}

.view-btn {
  padding: 8px 12px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 16px;
  color: #323130;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid #8a8886;
}

.view-btn:last-child {
  border-right: none;
}

.view-btn:hover {
  background-color: #f3f2f1;
  color: #201f1e;
}

.view-btn.active {
  background-color: rgb(58, 126, 185);
  color: white;
  box-shadow: inset 0 2px 4px rgba(58, 126, 185, 0.3);
}

.view-btn.active:hover {
  background-color: rgb(45, 102, 150);
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 8px 16px;
  border: 1px solid #8a8886;
  border-radius: var(--waves-radius-sm);
  background: #ffffff;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  white-space: nowrap;
  color: #323130;
  font-weight: 400;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background-color: #f3f2f1;
  border-color: #605e5c;
  color: #201f1e;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.action-btn:active {
  background-color: #edebe9;
  border-color: #323130;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #f3f2f1;
  color: #a19f9d;
  border-color: #c8c6c4;
}

.action-btn.primary {
  background-color: rgb(58, 126, 185);
  color: white;
  border-color: rgb(58, 126, 185);
  box-shadow: 0 2px 4px rgba(58, 126, 185, 0.3);
}

.action-btn.primary:hover {
  background-color: rgb(45, 102, 150);
  border-color: rgb(45, 102, 150);
  box-shadow: 0 4px 8px rgba(45, 102, 150, 0.35);
}

.action-btn.primary:active {
  background-color: rgb(37, 83, 121);
  border-color: rgb(37, 83, 121);
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
