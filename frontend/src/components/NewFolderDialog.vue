<template>
  <div class="waves-folder-dialog">
    <div class="waves-dialog-container">
      <!-- 对话框头部 -->
      <div class="waves-dialog-header">
        <div class="waves-header-content">
          <div class="waves-header-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 19C22 19.5304 21.7893 20.0391 21.4142 20.4142C21.0391 20.7893 20.5304 21 20 21H4C3.46957 21 2.96086 20.7893 2.58579 20.4142C2.21071 20.0391 2 19.5304 2 19V5C2 4.46957 2.21071 3.96086 2.58579 3.58579C2.96086 3.21071 3.46957 3 4 3H9L11 6H20C20.5304 6 21.0391 6.21071 21.4142 6.58579C21.7893 6.96086 22 7.46957 22 8V19Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 14L12 10M10 12L14 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="waves-header-text">
            <h3 class="waves-dialog-title">新建文件夹</h3>
          </div>
        </div>
        <button @click="$emit('close')" class="waves-close-btn">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      
      <!-- 对话框主体 -->
      <div class="waves-dialog-body">
        <div class="waves-form-section">
          
          <div class="waves-form-group">
            <label class="waves-form-label">
              <span class="waves-label-text">文件夹名称</span>
            </label>
            <div class="waves-input-container">
              <input
                v-model="folderName"
                type="text"
                class="waves-form-control"
                :class="{ 'waves-has-error': hasError }"
                placeholder="请输入文件夹名称"
                @keyup.enter="createFolder"
                @input="validateInput"
                ref="nameInput"
              />
              <div v-if="folderName.trim()" class="waves-input-clear" @click="clearInput">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <path d="M15 9L9 15M9 9L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            <div v-if="hasError" class="waves-form-error">
              <svg class="waves-error-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M15 9L9 15M9 9L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span class="waves-error-text">{{ errorMessage }}</span>
            </div>
            <div v-else-if="folderName.trim()" class="waves-form-success">
              <svg class="waves-success-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span class="waves-success-text">文件夹名称有效</span>
            </div>
          </div>
          

        </div>
      </div>
      
      <!-- 对话框底部 -->
      <div class="waves-dialog-footer">
        <button @click="$emit('close')" class="waves-btn waves-btn-secondary">
          取消
        </button>
        <button 
          @click="createFolder" 
          class="waves-btn waves-btn-primary" 
          :disabled="!folderName.trim() || creating || hasError"
        >
          {{ creating ? '创建中...' : '创建文件夹' }}
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
    const hasError = ref(false)
    const errorMessage = ref('')
    
    const currentFolderId = computed(() => filesStore.currentFolderId)
    
    onMounted(() => {
      // 自动聚焦到输入框
      nextTick(() => {
        nameInput.value?.focus()
      })
    })
    
    const validateInput = () => {
      const name = folderName.value.trim()
      
      if (!name) {
        hasError.value = false
        errorMessage.value = ''
        return
      }
      
      // 检查文件夹名称是否包含非法字符
      const invalidChars = /[<>:"/\\|?*]/
      if (invalidChars.test(name)) {
        hasError.value = true
        errorMessage.value = '文件夹名称不能包含以下字符: < > : " / \\ | ? *'
        return
      }
      
      // 检查文件夹名称长度
      if (name.length > 255) {
        hasError.value = true
        errorMessage.value = '文件夹名称不能超过255个字符'
        return
      }
      
      // 检查是否为保留名称
      const reservedNames = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
      if (reservedNames.includes(name.toUpperCase())) {
        hasError.value = true
        errorMessage.value = '不能使用系统保留名称'
        return
      }
      
      hasError.value = false
      errorMessage.value = ''
    }
    
    const clearInput = () => {
      folderName.value = ''
      hasError.value = false
      errorMessage.value = ''
      nameInput.value?.focus()
    }
    
    const createFolder = async () => {
      if (!folderName.value.trim() || creating.value || hasError.value) return
      
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
      hasError,
      errorMessage,
      currentFolderId,
      validateInput,
      clearInput,
      createFolder
    }
  }
}
</script>

<style scoped>
/* 企业级新建文件夹对话框样式 */
.waves-folder-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: waves-fade-in 0.3s ease;
}

.waves-dialog-container {
  background: var(--waves-surface-primary);
  border-radius: var(--waves-radius-xl);
  box-shadow: var(--waves-shadow-2xl);
  max-width: 500px;
  width: 90vw;
  max-height: 90vh;
  overflow: hidden;
  animation: waves-scale-in 0.3s ease;
  border: 1px solid var(--waves-border-light);
}

@keyframes waves-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes waves-scale-in {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

/* 对话框头部 */
.waves-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 2rem;
  background: var(--waves-surface-primary);
  border-bottom: 1px solid var(--waves-border-light);
  position: relative;
}

.waves-header-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.waves-header-icon {
  width: 40px;
  height: 40px;
  background: var(--waves-primary-500);
  border-radius: var(--waves-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: var(--waves-shadow-sm);
}

.waves-header-icon svg {
  width: 20px;
  height: 20px;
}

.waves-header-text {
  flex: 1;
}

.waves-dialog-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 0.25rem 0;
}

.waves-dialog-subtitle {
  font-size: 0.875rem;
  color: #e0e0e0;
  margin: 0;
  line-height: 1.4;
}

.waves-close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--waves-surface-secondary);
  border-radius: var(--waves-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #e0e0e0;
}

.waves-close-btn:hover {
  background: #fee;
  color: #d13438;
}

.waves-close-btn svg {
  width: 16px;
  height: 16px;
}

/* 对话框主体 */
.waves-dialog-body {
  padding: 2rem;
  max-height: 60vh;
  overflow-y: auto;
}

/* 表单区域 */
.waves-form-section {
  background: var(--waves-surface-secondary);
  border-radius: var(--waves-radius-lg);
  border: 1px solid var(--waves-border-light);
  overflow: hidden;
}



.waves-form-group {
  padding: 1.5rem;
}

.waves-form-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
  font-weight: 500;
  color: #ffffff;
  font-size: 0.875rem;
}

.waves-label-text {
  color: #ffffff;
}

.waves-label-required {
  color: var(--waves-error-500);
  font-weight: 600;
}

.waves-input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.waves-input-icon {
  position: absolute;
  left: 1rem;
  width: 16px;
  height: 16px;
  color: var(--waves-text-secondary);
  z-index: 1;
  pointer-events: none;
}

.waves-form-control {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.75rem;
  border: 2px solid var(--waves-border-light);
  border-radius: var(--waves-radius-md);
  font-size: 0.875rem;
  transition: all 0.3s ease;
  box-sizing: border-box;
  background: var(--waves-surface-primary);
  color: #ffffff;
  font-family: inherit;
}

.waves-form-control::placeholder {
  color: #e0e0e0;
  opacity: 1;
}

.waves-form-control:focus {
  outline: none;
  border-color: var(--waves-primary-500);
  box-shadow: 0 0 0 3px rgba(var(--waves-primary-rgb), 0.1);
  background: var(--waves-surface-primary);
}

.waves-form-control.waves-has-error {
  border-color: var(--waves-error-500);
  background: var(--waves-error-25);
}

.waves-form-control.waves-has-error:focus {
  border-color: var(--waves-error-500);
  box-shadow: 0 0 0 3px rgba(var(--waves-error-rgb), 0.1);
}

.waves-input-clear {
  position: absolute;
  right: 1rem;
  width: 16px;
  height: 16px;
  color: var(--waves-text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1;
}

.waves-input-clear:hover {
  color: var(--waves-error-500);
  transform: scale(1.1);
}

.waves-input-clear svg {
  width: 16px;
  height: 16px;
}

/* 表单验证消息 */
.waves-form-error,
.waves-form-success {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  line-height: 1.4;
}

.waves-form-error {
  color: var(--waves-error-600);
}

.waves-form-success {
  color: #4ade80;
}

.waves-error-icon,
.waves-success-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}



/* 对话框底部 */
.waves-dialog-footer {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding: 2rem;
  background: var(--waves-surface-secondary);
  border-top: 1px solid var(--waves-border-light);
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
  font-size: 0.875rem;
  min-width: 120px;
  justify-content: center;
}



.waves-btn-primary {
  background: var(--waves-primary-600);
  color: white;
}

.waves-btn-primary:hover:not(:disabled) {
  background: var(--waves-primary-700);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-md);
}

.waves-btn-primary:disabled {
  background: var(--waves-surface-tertiary);
  color: var(--waves-text-disabled);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.waves-btn-secondary {
  background: var(--waves-surface-primary);
  color: #ffffff;
  border: 1px solid var(--waves-border-light);
}

.waves-btn-secondary:hover {
  background: var(--waves-surface-secondary);
  border-color: var(--waves-primary-300);
  transform: translateY(-2px);
  box-shadow: var(--waves-shadow-md);
}



/* 滚动条样式 */
.waves-dialog-body::-webkit-scrollbar {
  width: 8px;
}

.waves-dialog-body::-webkit-scrollbar-track {
  background: var(--waves-surface-secondary);
  border-radius: var(--waves-radius-sm);
}

.waves-dialog-body::-webkit-scrollbar-thumb {
  background: var(--waves-border-light);
  border-radius: var(--waves-radius-sm);
}

.waves-dialog-body::-webkit-scrollbar-thumb:hover {
  background: var(--waves-primary-400);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .waves-dialog-container {
    width: 95vw;
    max-height: 95vh;
  }
  
  .waves-dialog-header,
  .waves-dialog-body,
  .waves-dialog-footer {
    padding: 1.5rem;
  }
  
  .waves-form-group {
    padding: 1rem;
  }
  
  .waves-dialog-footer {
    flex-direction: column;
  }
  
  .waves-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .waves-dialog-header {
    padding: 1rem;
  }
  
  .waves-header-icon {
    width: 40px;
    height: 40px;
  }
  
  .waves-header-icon svg {
    width: 20px;
    height: 20px;
  }
  
  .waves-dialog-title {
    font-size: 1.125rem;
  }
  
  .waves-dialog-subtitle {
    font-size: 0.8rem;
  }
}
</style>