<template>
  <div class="enhanced-upload-dialog">
    <div class="dialog-container">
      <!-- 对话框头部 -->
      <div class="dialog-header">
        <h2>📤 文件上传</h2>
        <button @click="$emit('close')" class="close-btn">✕</button>
      </div>

      <!-- 对话框内容 -->
      <div class="dialog-content">
        <!-- 步骤指示器 -->
        <div class="step-indicator">
          <div class="step" :class="{ active: currentStep === 1, completed: currentStep > 1 }">
            <span class="step-number">1</span>
            <span class="step-label">选择文件</span>
          </div>
          <div class="step-divider"></div>
          <div class="step" :class="{ active: currentStep === 2, completed: currentStep > 2 }">
            <span class="step-number">2</span>
            <span class="step-label">填写信息</span>
          </div>
          <div class="step-divider"></div>
          <div class="step" :class="{ active: currentStep === 3 }">
            <span class="step-number">3</span>
            <span class="step-label">确认上传</span>
          </div>
        </div>

        <!-- 步骤1: 文件选择 -->
        <div v-if="currentStep === 1" class="step-content">
          <div 
            class="upload-zone" 
            :class="{ 'drag-over': isDragOver, 'has-files': selectedFiles.length > 0 }"
            @drop="handleDrop" 
            @dragover.prevent="handleDragOver" 
            @dragleave.prevent="handleDragLeave"
            @click="selectFiles"
          >
            <input
              ref="fileInput"
              type="file"
              multiple
              @change="handleFileSelect"
              style="display: none"
            />
            
            <div class="upload-content">
              <div class="upload-icon">📁</div>
              <h3>拖拽文件到此处或点击选择</h3>
              <p>支持多个文件同时上传，单个文件最大 100GB</p>
              <p class="supported-formats">
                支持格式: FASTA, FASTQ, VCF, BAM, PDF, CSV, Python, Jupyter Notebook 等
              </p>
            </div>
          </div>
          
          <!-- 文件列表 -->
          <div v-if="selectedFiles.length > 0" class="file-list">
            <h4>已选择文件 ({{ selectedFiles.length }})</h4>
            <div class="file-items">
              <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
                <div class="file-icon">{{ getFileIcon(file.name) }}</div>
                <div class="file-info">
                  <div class="file-name">{{ file.name }}</div>
                  <div class="file-meta">
                    <span>{{ formatFileSize(file.size) }}</span>
                    <span>{{ detectFileFormat(file.name) }}</span>
                  </div>
                </div>
                <button @click="removeFile(index)" class="remove-btn">🗑️</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 步骤2: 元数据填写 -->
        <div v-if="currentStep === 2" class="step-content">
          <div class="metadata-form">
            <h3>📋 文件信息</h3>
            <p class="form-description">请填写文件的基本信息，这将帮助您更好地管理和搜索文件。</p>
            
            <div class="form-grid">
              <!-- 必填字段 -->
              <div class="form-section">
                <h4>📌 必填信息</h4>
                
                <div class="form-group">
                  <label for="title">文件标题 *</label>
                  <input
                    id="title"
                    v-model="metadata.title"
                    type="text"
                    placeholder="请输入文件的描述性标题"
                    required
                  />
                  <small>例如: 人类基因组RNA-seq数据分析结果</small>
                </div>
                
                <div class="form-group">
                  <label for="project">项目名称 *</label>
                  <input
                    id="project"
                    v-model="metadata.project"
                    type="text"
                    placeholder="项目名或课题号"
                    required
                  />
                  <small>例如: MyLab-2024-001 或 癌症基因组学研究</small>
                </div>
                
                <div class="form-row">
                  <div class="form-group">
                    <label for="document_type">文档类型 *</label>
                    <select id="document_type" v-model="metadata.document_type" required>
                      <option value="">请选择</option>
                      <option value="Paper">Paper</option>
                      <option value="Protocol">Protocol</option>
                      <option value="Dataset">Dataset</option>
                      <option value="Code">Code</option>
                    </select>
                  </div>
                  
                  <div class="form-group">
                    <label for="access_level">访问级别 *</label>
                    <select id="access_level" v-model="metadata.access_level" required>
                      <option value="">请选择</option>
                      <option value="Public">Public</option>
                      <option value="Internal">Internal</option>
                      <option value="Restricted">Restricted</option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- 可选字段 -->
              <div class="form-section">
                <h4>🔬 实验信息 (可选)</h4>
                
                <div class="form-group">
                  <label for="organism">物种</label>
                  <input
                    id="organism"
                    v-model="metadata.organism"
                    type="text"
                    placeholder="例如: Homo sapiens, Mus musculus"
                    list="organism-suggestions"
                  />
                  <datalist id="organism-suggestions">
                    <option value="Homo sapiens">Homo sapiens</option>
                    <option value="Mus musculus">Mus musculus</option>
                    <option value="Drosophila melanogaster">Drosophila melanogaster</option>
                    <option value="Caenorhabditis elegans">Caenorhabditis elegans</option>
                    <option value="Saccharomyces cerevisiae">Saccharomyces cerevisiae</option>
                    <option value="Escherichia coli">Escherichia coli</option>
                    <option value="Arabidopsis thaliana">Arabidopsis thaliana</option>
                  </datalist>
                  <small>支持NCBI标准物种名称</small>
                </div>
                
                <div class="form-group">
                  <label for="experiment_type">实验类型</label>
                  <select id="experiment_type" v-model="metadata.experiment_type">
                    <option value="">请选择</option>
                    <option value="RNA-seq">RNA-seq</option>
                    <option value="WGS">Whole Genome Sequencing</option>
                    <option value="scRNA-seq">Single Cell RNA-seq</option>
                    <option value="MS">Mass Spectrometry</option>
                    <option value="ChIP-seq">ChIP-seq</option>
                    <option value="ATAC-seq">ATAC-seq</option>
                    <option value="other">其他</option>
                  </select>
                </div>
                
                <div class="form-group">
                  <label for="tags">标签</label>
                  <input
                    id="tags"
                    v-model="metadata.tags"
                    type="text"
                    placeholder="用逗号分隔，例如: 癌症,基因组学,生物信息学"
                  />
                  <small>用逗号分隔多个标签</small>
                </div>
                
                <div class="form-group">
                  <label for="description">描述</label>
                  <textarea
                    id="description"
                    v-model="metadata.description"
                    rows="3"
                    placeholder="详细描述文件内容、实验条件、数据来源等"
                  ></textarea>
                </div>
              </div>
            </div>

            <!-- 自动检测的信息 -->
            <div v-if="detectedInfo.length > 0" class="detected-info">
              <h4>🤖 自动检测信息</h4>
              <div class="detected-items">
                <div v-for="info in detectedInfo" :key="info.file" class="detected-item">
                  <strong>{{ info.file }}:</strong>
                  <span>格式: {{ info.format }}</span>
                  <span v-if="info.organism">物种: {{ info.organism }}</span>
                  <span v-if="info.keywords">关键词: {{ info.keywords.join(', ') }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 步骤3: 确认上传 -->
        <div v-if="currentStep === 3" class="step-content">
          <div class="upload-summary">
            <h3>📋 上传确认</h3>
            
            <!-- 文件信息摘要 -->
            <div class="summary-section">
              <h4>文件列表</h4>
              <div class="summary-files">
                <div v-for="file in selectedFiles" :key="file.name" class="summary-file">
                  <span class="file-icon">{{ getFileIcon(file.name) }}</span>
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                </div>
              </div>
            </div>
            
            <!-- 元数据摘要 -->
            <div class="summary-section">
              <h4>文件信息</h4>
              <div class="summary-metadata">
                <div class="metadata-item">
                  <label>标题:</label>
                  <span>{{ metadata.title }}</span>
                </div>
                <div class="metadata-item">
                  <label>项目:</label>
                  <span>{{ metadata.project }}</span>
                </div>
                <div class="metadata-item">
                  <label>文档类型:</label>
                  <span>{{ metadata.document_type }}</span>
                </div>
                <div class="metadata-item">
                  <label>访问级别:</label>
                  <span>{{ metadata.access_level }}</span>
                </div>
                <div v-if="metadata.organism" class="metadata-item">
                  <label>物种:</label>
                  <span>{{ metadata.organism }}</span>
                </div>
                <div v-if="metadata.experiment_type" class="metadata-item">
                  <label>实验类型:</label>
                  <span>{{ metadata.experiment_type }}</span>
                </div>
                <div v-if="metadata.tags" class="metadata-item">
                  <label>标签:</label>
                  <span>{{ metadata.tags }}</span>
                </div>
                <div v-if="metadata.description" class="metadata-item">
                  <label>描述:</label>
                  <span>{{ metadata.description }}</span>
                </div>
              </div>
            </div>

            <!-- 上传进度 -->
            <div v-if="uploading" class="upload-progress">
              <div class="progress-info">
                <span>正在上传文件... ({{ currentFileIndex + 1 }}/{{ selectedFiles.length }})</span>
                <span>{{ uploadProgress }}%</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
              </div>
              <div class="current-file">
                当前文件: {{ selectedFiles[currentFileIndex]?.name }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 对话框底部 -->
      <div class="dialog-footer">
        <button 
          v-if="currentStep > 1" 
          @click="previousStep" 
          class="btn btn-secondary"
          :disabled="uploading"
        >
          上一步
        </button>
        
        <button @click="$emit('close')" class="btn btn-secondary" :disabled="uploading">
          取消
        </button>
        
        <button 
          v-if="currentStep < 3" 
          @click="nextStep" 
          class="btn btn-primary"
          :disabled="!canProceed"
        >
          下一步
        </button>
        
        <button 
          v-if="currentStep === 3" 
          @click="uploadFiles" 
          class="btn btn-primary"
          :disabled="uploading || !canUpload"
        >
          {{ uploading ? '上传中...' : '开始上传' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { useFilesStore } from '../stores/files'

export default {
  name: 'EnhancedUploadDialog',
  emits: ['close'],
  setup(props, { emit }) {
    const filesStore = useFilesStore()
    
    // 状态管理
    const currentStep = ref(1)
    const selectedFiles = ref([])
    const uploading = ref(false)
    const uploadProgress = ref(0)
    const currentFileIndex = ref(0)
    const isDragOver = ref(false)
    const fileInput = ref(null)
    
    // 元数据表单
    const metadata = reactive({
      title: '',
      project: '默认项目',
      document_type: 'Dataset',
      access_level: 'Internal',
      organism: '',
      experiment_type: '',
      tags: '',
      description: ''
    })
    
    // 自动检测信息
    const detectedInfo = ref([])
    
    // 计算属性
    const currentFolderId = computed(() => filesStore.currentFolderId)
    
    const canProceed = computed(() => {
      if (currentStep.value === 1) {
        return selectedFiles.value.length > 0
      }
      if (currentStep.value === 2) {
        return metadata.title && metadata.project && metadata.document_type && metadata.access_level
      }
      return true
    })
    
    const canUpload = computed(() => {
      return selectedFiles.value.length > 0 && canProceed.value
    })
    
    // 文件操作方法
    const selectFiles = () => {
      fileInput.value.click()
    }
    
    const handleFileSelect = (event) => {
      const files = Array.from(event.target.files)
      addFiles(files)
    }
    
    const handleDragOver = (event) => {
      event.preventDefault()
      isDragOver.value = true
    }
    
    const handleDragLeave = (event) => {
      event.preventDefault()
      isDragOver.value = false
    }
    
    const handleDrop = (event) => {
      event.preventDefault()
      isDragOver.value = false
      const files = Array.from(event.dataTransfer.files)
      addFiles(files)
    }
    
    const addFiles = (files) => {
      selectedFiles.value = [...selectedFiles.value, ...files]
      
      // 自动检测文件信息
      files.forEach(file => {
        const info = {
          file: file.name,
          format: detectFileFormat(file.name),
          organism: null,
          keywords: []
        }
        
        // 如果是第一个文件，自动填充一些信息
        if (selectedFiles.value.length === 1) {
          if (!metadata.title) {
            metadata.title = file.name.replace(/\.[^/.]+$/, '') // 去掉扩展名
          }
        }
        
        detectedInfo.value.push(info)
      })
    }
    
    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1)
      detectedInfo.value.splice(index, 1)
    }
    
    // 步骤控制
    const nextStep = () => {
      if (canProceed.value && currentStep.value < 3) {
        currentStep.value++
      }
    }
    
    const previousStep = () => {
      if (currentStep.value > 1) {
        currentStep.value--
      }
    }
    
    // 上传处理
    const uploadFiles = async () => {
      if (!canUpload.value) return
      
      uploading.value = true
      uploadProgress.value = 0
      currentFileIndex.value = 0
      
      try {
        const totalFiles = selectedFiles.value.length
        
        for (let i = 0; i < totalFiles; i++) {
          currentFileIndex.value = i
          const file = selectedFiles.value[i]
          
          // 为每个文件准备元数据
          const fileMetadata = {
            ...metadata,
            file_format: detectFileFormat(file.name)
          }
          
          // 监听上传进度
          const progressWatcher = watch(() => filesStore.uploadProgress, (progress) => {
            const fileProgress = (i / totalFiles) * 100 + (progress / totalFiles)
            uploadProgress.value = Math.round(fileProgress)
          })
          
          // 上传文件
          await filesStore.uploadFileWithMetadata(
            file,
            fileMetadata,
            currentFolderId.value
          )
          
          progressWatcher()
        }
        
        // 刷新文件列表
        await filesStore.fetchFiles(currentFolderId.value)
        
        // 关闭对话框
        emit('close')
        
      } catch (error) {
        console.error('上传失败:', error)
        alert('上传失败: ' + error.message)
      } finally {
        uploading.value = false
        uploadProgress.value = 0
        currentFileIndex.value = 0
      }
    }
    
    // 工具方法
    const detectFileFormat = (filename) => {
      const ext = filename.toLowerCase().split('.').pop()
      const formatMap = {
        // 生物信息学格式
        'fastq': 'FASTQ',
        'fq': 'FASTQ',
        'fasta': 'FASTA',
        'fa': 'FASTA',
        'vcf': 'VCF',
        'bam': 'BAM',
        'sam': 'SAM',
        'bed': 'BED',
        'gtf': 'GTF',
        'gff': 'GFF',
        
        // 文档格式
        'pdf': 'PDF',
        'doc': 'DOC',
        'docx': 'DOCX',
        'ppt': 'PPT',
        'pptx': 'PPTX',
        'rtf': 'RTF',
        
        // 数据格式
        'csv': 'CSV',
        'tsv': 'TSV',
        'xls': 'XLS',
        'xlsx': 'XLSX',
        'json': 'JSON',
        'xml': 'XML',
        'yaml': 'YAML',
        'yml': 'YAML',
        'sql': 'SQL',
        
        // 代码格式
        'py': 'py',
        'ipynb': 'ipynb',
        'r': 'R',
        'rmd': 'Rmd',
        'js': 'js',
        'html': 'html',
        'htm': 'html',
        'css': 'css',
        'java': 'java',
        'cpp': 'cpp',
        'cxx': 'cpp',
        'cc': 'cpp',
        'c': 'c',
        'h': 'c',
        'hpp': 'cpp',
        'sh': 'sh',
        'bash': 'sh',
        'zsh': 'sh',
        'pl': 'pl',
        'php': 'php',
        'rb': 'rb',
        'go': 'go',
        'rs': 'rs',
        'swift': 'swift',
        'kt': 'kt',
        'scala': 'scala',
        
        // 文本格式
        'txt': 'txt',
        'md': 'md',
        'markdown': 'md',
        'log': 'log',
        'conf': 'conf',
        'config': 'conf',
        'ini': 'ini',
        'cfg': 'cfg',
        
        // 图像格式
        'jpg': 'jpg',
        'jpeg': 'jpeg',
        'png': 'png',
        'gif': 'gif',
        'bmp': 'bmp',
        'tiff': 'tiff',
        'tif': 'tiff',
        'svg': 'svg',
        'webp': 'webp',
        'ico': 'ico',
        
        // 音频格式
        'mp3': 'mp3',
        'wav': 'wav',
        'flac': 'flac',
        'aac': 'aac',
        'ogg': 'ogg',
        'm4a': 'm4a',
        
        // 视频格式
        'mp4': 'mp4',
        'avi': 'avi',
        'mov': 'mov',
        'wmv': 'wmv',
        'flv': 'flv',
        'mkv': 'mkv',
        'webm': 'webm',
        'm4v': 'm4v',
        
        // 压缩格式
        'zip': 'zip',
        'rar': 'rar',
        '7z': '7z',
        'tar': 'tar',
        'gz': 'gz',
        'bz2': 'bz2',
        'xz': 'xz'
      }
      return formatMap[ext] || 'other'
    }
    
    const getFileIcon = (filename) => {
      const format = detectFileFormat(filename)
      const icons = {
        // 生物信息学格式
        'FASTQ': '🧬',
        'FASTA': '🧬',
        'VCF': '📊',
        'BAM': '📊',
        'SAM': '📊',
        'BED': '📊',
        'GTF': '📊',
        'GFF': '📊',
        
        // 文档格式
        'PDF': '📄',
        'DOC': '📝',
        'DOCX': '📝',
        'PPT': '📊',
        'PPTX': '📊',
        'RTF': '📝',
        
        // 数据格式
        'CSV': '📊',
        'TSV': '📊',
        'XLS': '📊',
        'XLSX': '📊',
        'JSON': '📋',
        'XML': '📋',
        'YAML': '📋',
        'SQL': '🗃️',
        
        // 代码格式
        'py': '🐍',
        'ipynb': '📓',
        'R': '📈',
        'Rmd': '📈',
        'js': '🟨',
        'html': '🌐',
        'css': '🎨',
        'java': '☕',
        'cpp': '⚙️',
        'c': '⚙️',
        'sh': '💻',
        'pl': '🔷',
        'php': '🐘',
        'rb': '💎',
        'go': '🐹',
        'rs': '🦀',
        'swift': '🍎',
        'kt': '🟣',
        'scala': '🔴',
        
        // 文本格式
        'txt': '📝',
        'md': '📝',
        'log': '📋',
        'conf': '⚙️',
        'ini': '⚙️',
        'cfg': '⚙️',
        
        // 图像格式
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️',
        'bmp': '🖼️',
        'tiff': '🖼️',
        'svg': '🖼️',
        'webp': '🖼️',
        'ico': '🖼️',
        
        // 音频格式
        'mp3': '🎵',
        'wav': '🎵',
        'flac': '🎵',
        'aac': '🎵',
        'ogg': '🎵',
        'm4a': '🎵',
        
        // 视频格式
        'mp4': '🎬',
        'avi': '🎬',
        'mov': '🎬',
        'wmv': '🎬',
        'flv': '🎬',
        'mkv': '🎬',
        'webm': '🎬',
        'm4v': '🎬',
        
        // 压缩格式
        'zip': '📦',
        'rar': '📦',
        '7z': '📦',
        'tar': '📦',
        'gz': '📦',
        'bz2': '📦',
        'xz': '📦'
      }
      return icons[format] || '📄'
    }
    
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    return {
      currentStep,
      selectedFiles,
      uploading,
      uploadProgress,
      currentFileIndex,
      isDragOver,
      fileInput,
      metadata,
      detectedInfo,
      canProceed,
      canUpload,
      selectFiles,
      handleFileSelect,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      removeFile,
      nextStep,
      previousStep,
      uploadFiles,
      detectFileFormat,
      getFileIcon,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.enhanced-upload-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.dialog-container {
  background: white;
  border-radius: 12px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.dialog-header h2 {
  margin: 0;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
  padding: 5px;
  border-radius: 4px;
  transition: background 0.3s;
}

.close-btn:hover {
  background: #e9ecef;
}

.dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e9ecef;
  color: #6c757d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all 0.3s;
}

.step.active .step-number {
  background: #3498db;
  color: white;
}

.step.completed .step-number {
  background: #28a745;
  color: white;
}

.step-label {
  font-size: 0.9rem;
  color: #6c757d;
  font-weight: 500;
}

.step.active .step-label {
  color: #3498db;
}

.step.completed .step-label {
  color: #28a745;
}

.step-divider {
  width: 60px;
  height: 2px;
  background: #e9ecef;
  margin: 0 20px;
}

.step-content {
  min-height: 400px;
}

/* 步骤1: 文件选择样式 */
.upload-zone {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 20px;
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: #3498db;
  background: #f8f9fa;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 15px;
}

.upload-content h3 {
  margin: 0 0 10px 0;
  color: #2c3e50;
}

.upload-content p {
  margin: 5px 0;
  color: #6c757d;
}

.supported-formats {
  font-size: 0.9rem;
  font-style: italic;
}

.file-list {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.file-list h4 {
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.file-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.file-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.file-info {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 5px;
}

.file-meta {
  display: flex;
  gap: 15px;
  color: #6c757d;
  font-size: 0.9rem;
}

.remove-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: background 0.3s;
}

.remove-btn:hover {
  background: #f8d7da;
}

/* 步骤2: 元数据表单样式 */
.metadata-form {
  max-width: 800px;
}

.metadata-form h3 {
  margin: 0 0 10px 0;
  color: #2c3e50;
}

.form-description {
  color: #6c757d;
  margin-bottom: 30px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.form-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.form-section h4 {
  margin: 0 0 20px 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #495057;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

.form-group small {
  display: block;
  margin-top: 5px;
  color: #6c757d;
  font-size: 0.8rem;
}

.detected-info {
  margin-top: 30px;
  padding: 20px;
  background: #e8f5e8;
  border-radius: 8px;
}

.detected-info h4 {
  margin: 0 0 15px 0;
  color: #28a745;
}

.detected-items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detected-item {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  font-size: 0.9rem;
}

.detected-item strong {
  color: #2c3e50;
}

.detected-item span {
  color: #6c757d;
}

/* 步骤3: 确认上传样式 */
.upload-summary {
  max-width: 700px;
}

.summary-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.summary-section h4 {
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.summary-files {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-file {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.summary-metadata {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.metadata-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.metadata-item label {
  font-weight: 500;
  color: #495057;
  font-size: 0.9rem;
}

.metadata-item span {
  color: #6c757d;
}

.upload-progress {
  margin-top: 20px;
  padding: 20px;
  background: #e8f4fd;
  border-radius: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-weight: 500;
  color: #2c3e50;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: #3498db;
  transition: width 0.3s;
}

.current-file {
  color: #6c757d;
  font-size: 0.9rem;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  padding: 20px;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dialog-container {
    width: 95vw;
    height: 95vh;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .summary-metadata {
    grid-template-columns: 1fr;
  }
  
  .step-indicator {
    flex-direction: column;
    gap: 15px;
  }
  
  .step-divider {
    width: 2px;
    height: 30px;
    margin: 0;
  }
}
</style>