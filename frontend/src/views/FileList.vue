<template>
  <div class="workspace">
    <header class="workspace-toolbar">
      <div class="toolbar-left">
        <div class="workspace-meta">
          <h1 class="workspace-title">文件工作台</h1>
          <div class="workspace-breadcrumb">
            <button v-if="currentFolderId !== null" class="breadcrumb-back" @click="navigateUp">
              返回上一级
            </button>
            <button class="breadcrumb-item" :class="{ active: currentFolderId === null }" @click="navigateToRoot">
              全部文件
            </button>
            <template v-for="(folder, index) in breadcrumbPath" :key="folder.id">
              <span class="breadcrumb-separator">/</span>
              <button
                class="breadcrumb-item"
                :class="{ active: index === breadcrumbPath.length - 1 }"
                @click="navigateToFolder(folder.id)"
              >
                {{ folder.name }}
              </button>
            </template>
          </div>
        </div>
      </div>
      <div class="toolbar-actions">
        <div class="view-switch">
          <button :class="{ active: viewMode === 'list' }" @click="setViewMode('list')">列表</button>
          <button :class="{ active: viewMode === 'grid' }" @click="setViewMode('grid')">画廊</button>
        </div>
        <button class="toolbar-btn ghost" @click="openSearch">查找</button>
        <button class="toolbar-btn primary" @click="showUploadDialogHandler">上传</button>
        <button class="toolbar-btn ghost" @click="showNewFolderDialogHandler">新建文件夹</button>
        <button class="toolbar-btn ghost" @click="refreshFiles" :disabled="isLoading">刷新</button>
      </div>
    </header>

    <div class="workspace-body">
      <aside class="workspace-panel">
        <div class="panel-title">目录导航</div>
        <div class="panel-content">
          <FolderTree />
        </div>
      </aside>

      <section class="workspace-canvas">
        <div class="canvas-surface">
          <div v-if="isLoading" class="canvas-overlay">
            <div class="overlay-card">
              <div class="spinner" />
              <p>正在加载文件列表…</p>
            </div>
          </div>
          <div v-else-if="error" class="canvas-overlay">
            <div class="overlay-card error">
              <h3>加载失败</h3>
              <p>{{ error }}</p>
              <div class="overlay-actions">
                <button @click="refreshFiles">重试</button>
                <button class="outline" @click="goHome">返回首页</button>
              </div>
            </div>
          </div>
          <div v-else class="canvas-content">
            <FileDisplay />
          </div>
        </div>
      </section>

      <aside class="workspace-insights">
        <div class="insight-card">
          <div class="insight-value">{{ currentFilesCount }}</div>
          <div class="insight-label">当前文件</div>
          <p class="insight-caption">实时统计本目录的文件数量，刷新后自动更新。</p>
        </div>
        <div class="insight-card">
          <div class="insight-value">{{ currentFoldersCount }}</div>
          <div class="insight-label">子文件夹</div>
          <p class="insight-caption">建议按项目、实验阶段划分子目录，便于权限管理。</p>
        </div>
        <div class="insight-card highlight">
          <div class="insight-value">{{ formattedTotalSize }}</div>
          <div class="insight-label">本层数据量</div>
          <p class="insight-caption">结合 Facets 搜索，可进一步筛查关注的数据集合。</p>
        </div>
      </aside>
    </div>

    <EnhancedUploadDialog v-if="showUploadDialog" @close="closeUploadDialog" />

    <div v-if="showNewFolderDialog" class="workspace-modal-overlay" @click="closeNewFolderDialog">
      <div class="workspace-modal" @click.stop>
        <NewFolderDialog @close="closeNewFolderDialog" />
      </div>
    </div>

    <Transition name="workspace-toast">
      <div v-if="successMessage" class="workspace-toast">
        <div class="toast-content">
          <strong>操作成功</strong>
          <span>{{ successMessage }}</span>
        </div>
        <button class="toast-close" @click="successMessage = ''">×</button>
      </div>
    </Transition>
  </div>
</template>

<script>
import { computed, ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useFilesStore } from '../stores/files'
import FolderTree from '../components/FolderTree.vue'
import FileDisplay from '../components/FileDisplay.vue'
import EnhancedUploadDialog from '../components/EnhancedUploadDialog.vue'
import NewFolderDialog from '../components/NewFolderDialog.vue'

export default {
  name: 'FileList',
  components: {
    FolderTree,
    FileDisplay,
    EnhancedUploadDialog,
    NewFolderDialog
  },
  setup() {
    const router = useRouter()
    const filesStore = useFilesStore()

    const successMessage = ref('')

    const isLoading = computed(() => filesStore.isLoading)
    const error = computed(() => filesStore.error)
    const showUploadDialog = computed(() => filesStore.showUploadDialog)
    const showNewFolderDialog = computed(() => filesStore.showNewFolderDialog)

    const currentFolderId = computed(() => filesStore.currentFolderId)
    const breadcrumbPath = computed(() => filesStore.breadcrumb || [])
    const viewMode = computed(() => filesStore.viewMode)

    const currentFiles = computed(() => filesStore.currentFiles || [])
    const currentFolders = computed(() => filesStore.currentFolders || [])
    const currentFilesCount = computed(() => currentFiles.value.length)
    const currentFoldersCount = computed(() => currentFolders.value.length)
    const totalSize = computed(() => currentFiles.value.reduce((sum, file) => sum + (file.file_size || 0), 0))

    const formatBytes = (bytes) => {
      if (!bytes) return '0 B'
      const units = ['B', 'KB', 'MB', 'GB', 'TB']
      const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
      const value = bytes / Math.pow(1024, exponent)
      return `${value.toFixed(value >= 10 || exponent === 0 ? 0 : 1)} ${units[exponent]}`
    }
    const formattedTotalSize = computed(() => formatBytes(totalSize.value))

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

    const showUploadDialogHandler = () => {
      filesStore.toggleUploadDialog()
    }

    const showNewFolderDialogHandler = () => {
      filesStore.toggleNewFolderDialog()
    }

    const closeUploadDialog = () => {
      filesStore.closeAllDialogs()
    }

    const closeNewFolderDialog = () => {
      filesStore.closeAllDialogs()
    }

    const refreshFiles = async () => {
      await filesStore.fetchFiles(currentFolderId.value)
    }

    const openSearch = () => {
      router.push('/search')
    }

    const goHome = () => {
      router.push('/')
    }

    const applyWorkspaceLayout = () => {
      nextTick(() => {
        const main = document.querySelector('main.container')
        if (main) {
          main.classList.add('workspace-main')
        }
      })
    }

    const resetWorkspaceLayout = () => {
      const main = document.querySelector('main.container')
      if (main) {
        main.classList.remove('workspace-main')
      }
    }

    onMounted(async () => {
      applyWorkspaceLayout()
      await filesStore.fetchFiles()
    })

    onBeforeUnmount(() => {
      resetWorkspaceLayout()
    })

    return {
      isLoading,
      error,
      showUploadDialog,
      showNewFolderDialog,
      successMessage,
      currentFolderId,
      breadcrumbPath,
      viewMode,
      currentFilesCount,
      currentFoldersCount,
      formattedTotalSize,
      navigateToRoot,
      navigateToFolder,
      navigateUp,
      setViewMode,
      showUploadDialogHandler,
      showNewFolderDialogHandler,
      closeUploadDialog,
      closeNewFolderDialog,
      refreshFiles,
      openSearch,
      goHome
    }
  }
}
</script>

<style scoped>
:global(main.workspace-main) {
  display: block;
  padding: 0;
  margin: 0;
  min-height: calc(100vh - 72px);
  width: 100%;
  max-width: none;
}

.workspace {
  min-height: calc(100vh - 72px);
  display: flex;
  flex-direction: column;
  background: var(--bg-light);
  width: 100%;
  overflow: hidden;
}

.workspace-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
  padding: 20px 32px 18px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(27, 44, 72, 0.06);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.workspace-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.workspace-title {
  font-size: 22px;
  font-weight: 650;
  margin: 0;
  color: var(--text-primary);
}

.workspace-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.breadcrumb-back {
  border: none;
  background: transparent;
  color: var(--primary);
  cursor: pointer;
  font-size: 13px;
  padding: 4px 0;
}

.breadcrumb-item {
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  padding: 4px 6px;
  border-radius: var(--radius-sm);
  transition: background 0.2s ease, color 0.2s ease;
}

.breadcrumb-item.active {
  color: var(--primary);
  font-weight: 600;
}

.breadcrumb-item:hover {
  background: rgba(65, 105, 225, 0.12);
  color: var(--primary);
}

.breadcrumb-separator {
  color: var(--text-muted);
  font-size: 12px;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.view-switch {
  display: inline-flex;
  border: 1px solid rgba(27, 44, 72, 0.12);
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: #fff;
}

.view-switch button {
  border: none;
  background: transparent;
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
  color: var(--text-muted);
  transition: background 0.2s ease, color 0.2s ease;
}

.view-switch button.active {
  background: var(--primary);
  color: #fff;
}

.toolbar-btn {
  border: 1px solid rgba(27, 44, 72, 0.12);
  background: #ffffff;
  color: var(--text-secondary);
  padding: 8px 18px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.toolbar-btn.primary {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.toolbar-btn.ghost {
  background: transparent;
  color: var(--text-secondary);
}

.toolbar-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.toolbar-btn:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(27, 44, 72, 0.12);
}

.workspace-body {
  flex: 1;
  display: flex;
  align-items: stretch;
  overflow: hidden;
  background: var(--bg-light);
  width: 100%;
  min-height: calc(100vh - 72px);
}

.workspace-panel {
  width: 272px;
  background: #ffffff;
  border-right: 1px solid rgba(27, 44, 72, 0.08);
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: calc(100vh - 72px);
}

.panel-title {
  padding: 18px 24px 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
  min-height: 0;
  background: #ffffff;
}

.workspace-canvas {
  flex: 1;
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.canvas-surface {
  flex: 1;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 20px 48px rgba(15, 31, 68, 0.08);
  position: relative;
  overflow: hidden;
  padding: 24px;
  display: flex;
  flex-direction: column;
}

.canvas-content {
  flex: 1;
  display: flex;
  min-height: 0;
}

.canvas-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(6px);
  display: flex;
  justify-content: center;
  align-items: center;
  zIndex: 2;
}

.overlay-card {
  background: #fff;
  border-radius: 16px;
  padding: 28px 36px;
  box-shadow: 0 18px 40px rgba(65, 105, 225, 0.16);
  text-align: center;
  color: var(--text-secondary);
}

.overlay-card.error {
  border: 1px solid rgba(244, 63, 94, 0.3);
}

.overlay-card h3 {
  margin-top: 0;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.overlay-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 18px;
}

.overlay-actions button {
  border: 1px solid var(--primary);
  background: var(--primary);
  color: #fff;
  border-radius: var(--radius-lg);
  padding: 8px 20px;
  cursor: pointer;
}

.overlay-actions button.outline {
  background: transparent;
  color: var(--primary);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(65, 105, 225, 0.18);
  border-top-color: var(--primary);
  border-radius: 50%;
  margin: 0 auto 16px;
  animation: spin 0.9s linear infinite;
}

.workspace-insights {
  width: 260px;
  border-left: 1px solid rgba(27, 44, 72, 0.08);
  background: rgba(255, 255, 255, 0.9);
  padding: 28px 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.insight-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 12px 30px rgba(27, 44, 72, 0.08);
}

.insight-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--primary);
}

.insight-label {
  font-size: 13px;
  color: var(--text-muted);
}

.insight-caption {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

.workspace-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.workspace-modal {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.25);
  max-width: 520px;
  width: 100%;
  overflow: hidden;
}

.workspace-toast {
  position: fixed;
  right: 28px;
  bottom: 32px;
  background: #111827;
  color: #fff;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 18px 40px rgba(15, 31, 68, 0.22);
  display: flex;
  align-items: center;
  gap: 16px;
  z-index: 20;
}

.toast-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.toast-close {
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-size: 20px;
  cursor: pointer;
}

.workspace-toast-enter-active,
.workspace-toast-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.workspace-toast-enter-from,
.workspace-toast-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

:deep(.waves-file-display) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

:deep(.waves-table-content) {
  flex: 1;
  overflow: auto;
}

@media (max-width: 1280px) {
  .workspace-insights {
    display: none;
  }
}

@media (max-width: 960px) {
  .workspace-toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  .workspace-body {
    flex-direction: column;
  }

  .workspace-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(27, 44, 72, 0.08);
  }

  .workspace-canvas {
    padding: 16px;
  }
}
</style>
