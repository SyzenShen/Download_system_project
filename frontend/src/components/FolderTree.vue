<template>
  <div class="folder-tree">
    <div class="tree-header">
      <h3>📁 我的文件</h3>
    </div>
    
    <div class="tree-content">
      <!-- 根目录 -->
      <div 
        class="tree-node root-node"
        :class="{ active: currentFolderId === null }"
        @click="navigateToRoot"
      >
        <span class="node-icon">🏠</span>
        <span class="node-label">全部文件</span>
      </div>
      
      <!-- 文件夹树 -->
      <div class="folder-nodes">
        <FolderNode
          v-for="folder in rootFolders"
          :key="folder.id"
          :folder="folder"
          :current-folder-id="currentFolderId"
          :expanded-folders="expandedFolders"
          :all-folders="allFolders"
          @navigate="handleNavigate"
          @toggle="handleToggle"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useFilesStore } from '../stores/files'
import FolderNode from './FolderNode.vue'

const filesStore = useFilesStore()

// 响应式数据
const expandedFolders = ref(new Set())
const allFolders = ref([]) // 存储所有文件夹

// 计算属性
const currentFolderId = computed(() => filesStore.currentFolderId)
const rootFolders = computed(() => {
  // 获取根级文件夹（没有父文件夹的）
  return allFolders.value.filter(folder => !folder.parent)
})

// 方法
const navigateToRoot = () => {
  filesStore.navigateToFolder(null)
}

const handleNavigate = (folderId) => {
  filesStore.navigateToFolder(folderId)
}

const handleToggle = (folderId) => {
  if (expandedFolders.value.has(folderId)) {
    expandedFolders.value.delete(folderId)
  } else {
    expandedFolders.value.add(folderId)
  }
}

// 加载所有文件夹
const loadAllFolders = async () => {
  try {
    const response = await fetch('/api/files/folders/all/', {
      headers: {
        'Authorization': `Token ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      allFolders.value = data.folders || []
    } else {
      console.error('加载文件夹失败:', response.statusText)
    }
  } catch (error) {
    console.error('加载文件夹失败:', error)
  }
}

// 智能展开到当前文件夹的路径，同时关闭不需要的文件夹
const expandToCurrentFolder = () => {
  // 如果没有当前文件夹，清空所有展开状态
  if (!currentFolderId.value) {
    expandedFolders.value.clear()
    return
  }
  
  // 找到当前文件夹
  const currentFolder = allFolders.value.find(f => f.id === currentFolderId.value)
  if (!currentFolder) {
    expandedFolders.value.clear()
    return
  }
  
  // 计算需要展开的路径（从根到当前文件夹的父级路径）
  const pathToExpand = new Set()
  let folder = currentFolder
  
  while (folder && folder.parent) {
    pathToExpand.add(folder.parent)
    folder = allFolders.value.find(f => f.id === folder.parent)
  }
  
  // 只保留需要展开的文件夹，关闭其他所有文件夹
  expandedFolders.value = pathToExpand
}

// 监听当前文件夹变化，自动展开路径
watch(currentFolderId, () => {
  expandToCurrentFolder()
}, { immediate: true })

// 监听allFolders变化，确保在数据加载后展开路径
watch(allFolders, () => {
  expandToCurrentFolder()
}, { immediate: true })

// 生命周期
onMounted(async () => {
  // 加载所有文件夹
  await loadAllFolders()
  // 初始化时加载当前目录的文件
  await filesStore.fetchFiles(currentFolderId.value)
})
</script>

<style scoped>
.folder-tree {
  width: 250px;
  height: 100%;
  background: #f8f9fa;
  border-right: 1px solid #e9ecef;
  display: flex;
  flex-direction: column;
}

.tree-header {
  padding: 16px;
  border-bottom: 1px solid #e9ecef;
  background: #fff;
}

.tree-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.tree-node {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  user-select: none;
}

.tree-node:hover {
  background-color: #e9ecef;
}

.tree-node.active {
  background-color: #007bff;
  color: white;
}

.tree-node.active:hover {
  background-color: #0056b3;
}

.root-node {
  font-weight: 600;
  margin-bottom: 8px;
}

.node-icon {
  margin-right: 8px;
  font-size: 16px;
}

.node-label {
  flex: 1;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.folder-nodes {
  padding-left: 0;
}

/* 滚动条样式 */
.tree-content::-webkit-scrollbar {
  width: 6px;
}

.tree-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.tree-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.tree-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>