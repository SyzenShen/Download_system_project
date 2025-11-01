<template>
  <div class="upload-test">
    <h2>文件上传测试</h2>
    
    <div class="test-section">
      <h3>认证状态</h3>
      <p>Token: {{ token ? '已设置' : '未设置' }}</p>
      <p>用户: {{ userInfo ? userInfo.username : '未登录' }}</p>
    </div>
    
    <div class="test-section">
      <h3>上传测试</h3>
      <input type="file" @change="handleFileSelect" />
      <button @click="testUpload" :disabled="!selectedFile || uploading">
        {{ uploading ? '上传中...' : '测试上传' }}
      </button>
    </div>
    
    <div class="test-section" v-if="uploadResult">
      <h3>上传结果</h3>
      <pre>{{ uploadResult }}</pre>
    </div>
    
    <div class="test-section" v-if="uploadError">
      <h3>上传错误</h3>
      <pre>{{ uploadError }}</pre>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'UploadTest',
  setup() {
    const authStore = useAuthStore()
    const token = ref(localStorage.getItem('token'))
    const userInfo = ref(null)
    const selectedFile = ref(null)
    const uploading = ref(false)
    const uploadResult = ref('')
    const uploadError = ref('')
    
    onMounted(async () => {
      try {
        await authStore.fetchUser()
        userInfo.value = authStore.user
      } catch (error) {
        console.error('获取用户信息失败:', error)
      }
    })
    
    const handleFileSelect = (event) => {
      selectedFile.value = event.target.files[0]
      uploadResult.value = ''
      uploadError.value = ''
    }
    
    const testUpload = async () => {
      if (!selectedFile.value) return
      
      uploading.value = true
      uploadResult.value = ''
      uploadError.value = ''
      
      try {
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        formData.append('title', '测试文件')
        formData.append('project', '测试项目')
        formData.append('file_format', 'txt')
        formData.append('document_type', 'Dataset')
        formData.append('access_level', 'Internal')
        formData.append('upload_method', 'Upload Test Page')
        
        const response = await fetch('/api/files/upload/', {
          method: 'POST',
          headers: {
            'Authorization': `Token ${token.value}`
          },
          body: formData
        })
        
        const responseText = await response.text()
        
        if (response.ok) {
          uploadResult.value = JSON.stringify(JSON.parse(responseText), null, 2)
        } else {
          uploadError.value = `状态码: ${response.status}\n响应: ${responseText}`
        }
        
      } catch (error) {
        uploadError.value = `错误: ${error.message}`
      } finally {
        uploading.value = false
      }
    }
    
    return {
      token,
      userInfo,
      selectedFile,
      uploading,
      uploadResult,
      uploadError,
      handleFileSelect,
      testUpload
    }
  }
}
</script>

<style scoped>
.upload-test {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.test-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.test-section h3 {
  margin-top: 0;
  color: #333;
}

pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
}

button {
  padding: 10px 20px;
  margin-left: 10px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

input[type="file"] {
  margin-bottom: 10px;
}
</style>