<template>
  <div class="folder-node-container">
    <div 
      class="folder-node"
      :class="{ 
        active: currentFolderId === folder.id,
        'has-children': hasChildren
      }"
      :style="{ paddingLeft: `${(level * 20) + 16}px` }"
      @click="handleClick"
    >
      <!-- 展开/收起图标 -->
      <span 
        v-if="hasChildren"
        class="expand-icon"
        :class="{ expanded: isExpanded }"
        @click.stop="handleToggle"
      >
        ▶
      </span>
      <span v-else class="expand-placeholder"></span>
      

      
      <!-- 文件夹名称 -->
      <span class="folder-name" :title="folder.name">
        {{ folder.name }}
      </span>
    </div>
    
    <!-- 子文件夹 -->
    <div v-if="isExpanded && hasChildren" class="children">
      <FolderNode
        v-for="child in children"
        :key="child.id"
        :folder="child"
        :current-folder-id="currentFolderId"
        :expanded-folders="expandedFolders"
        :all-folders="allFolders"
        :level="level + 1"
        @navigate="$emit('navigate', $event)"
        @toggle="$emit('toggle', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  folder: {
    type: Object,
    required: true
  },
  currentFolderId: {
    type: [Number, String],
    default: null
  },
  expandedFolders: {
    type: Set,
    required: true
  },
  allFolders: {
    type: Array,
    required: true
  },
  level: {
    type: Number,
    default: 0
  }
})

// Emits
const emit = defineEmits(['navigate', 'toggle'])

// 计算属性
const isExpanded = computed(() => {
  return props.expandedFolders.has(props.folder.id)
})

const children = computed(() => {
  // 从allFolders中获取当前文件夹的子文件夹
  return props.allFolders.filter(f => f.parent === props.folder.id)
})

const hasChildren = computed(() => {
  return children.value.length > 0
})

// 方法
const handleClick = () => {
  emit('navigate', props.folder.id)
}

const handleToggle = () => {
  emit('toggle', props.folder.id)
}
</script>

<style scoped>
.folder-node-container {
  width: 100%;
}

.folder-node {
  display: flex;
  align-items: center;
  padding: 6px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  user-select: none;
  min-height: 32px;
  color: var(--text-secondary);
}

.folder-node:hover {
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.folder-node.active {
  background-color: #0078d4;
  color: white;
  border-radius: var(--waves-radius-sm);
  box-shadow: 0 2px 4px rgba(0, 120, 212, 0.3);
}

.folder-node.active:hover {
  background-color: #106ebe;
}

.expand-icon {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 4px;
  font-size: 10px;
  transition: transform 0.2s;
  cursor: pointer;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.expand-placeholder {
  width: 16px;
  margin-right: 4px;
}

.folder-icon {
  margin-right: 8px;
  font-size: 14px;
}

.folder-name {
  flex: 1;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.children {
  width: 100%;
}

/* 活动状态下的图标颜色 */
.folder-node.active .expand-icon,
.folder-node.active .folder-icon {
  color: white;
}
</style>