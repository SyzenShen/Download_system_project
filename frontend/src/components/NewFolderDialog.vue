<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-dialog" @click.stop>
      <div class="modal-header">
        <h3>新建文件夹</h3>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label class="form-label">文件夹名称</label>
          <input
            v-model="folderName"
            type="text"
            class="form-control"
            placeholder="请输入文件夹名称"
            @keyup.enter="createFolder"
            ref="nameInput"
          />
        </div>
      </div>
      <div class="modal-footer">
        <button @click="$emit('close')" class="btn btn-secondary">取消</button>
        <button 
          @click="createFolder" 
          class="btn btn-primary" 
          :disabled="!folderName.trim() || creating"
        >
          {{ creating ? '创建中...' : '创建' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, nextTick, onMounted } from 'vue'
import { useFilesStore } from '../stores/files'

export default {
  name: 'NewFolderDialog',
  emits: ['close'],
  setup(props, { emit }) {
    const filesStore = useFilesStore()
    const folderName = ref('')
    const creating = ref(false)
    const nameInput = ref(null)
    
    const currentFolderId = computed(() => filesStore.currentFolderId)
    
    onMounted(() => {
      // 自动聚焦到输入框
      nextTick(() => {
        nameInput.value?.focus()
      })
    })
    
    const createFolder = async () => {
      if (!folderName.value.trim() || creating.value) return
      
      creating.value = true
      
      try {
        const result = await filesStore.createFolder(
          folderName.value.trim(),
          currentFolderId.value
        )
        
        if (result.success) {
          await filesStore.fetchFiles(currentFolderId.value)
          emit('close')
        } else {
          throw new Error(result.error)
        }
      } catch (error) {
        console.error('创建文件夹失败:', error)
        alert('创建文件夹失败: ' + error.message)
      } finally {
        creating.value = false
      }
    }
    
    return {
      folderName,
      creating,
      nameInput,
      currentFolderId,
      createFolder
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
  max-width: 400px;
  width: 90%;
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
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #e8e8e8;
  background: #fafafa;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #262626;
  font-size: 14px;
}

.form-control {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s ease;
  box-sizing: border-box;
}

.form-control:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
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