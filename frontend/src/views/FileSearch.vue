<template>
  <div class="file-search-container">
    <!-- 页面标题 -->
    <div class="search-header">
      <h1>🔍 文件查找</h1>
      <p class="search-subtitle">使用关键词搜索和筛选器快速找到您需要的文件</p>
    </div>

    <!-- 搜索框 -->
    <div class="search-box-container">
      <div class="search-box">
        <input
          v-model="searchQuery"
          @keyup.enter="performSearch"
          @input="onSearchInput"
          type="text"
          placeholder="搜索文件... (支持 project:MyLab organism:human 等高级语法)"
          class="search-input"
        />
        <button @click="performSearch" class="search-button">
          <span v-if="!isSearching">搜索</span>
          <span v-else>搜索中...</span>
        </button>
      </div>
      
      <!-- 搜索建议 -->
      <div v-if="suggestions.length > 0" class="search-suggestions">
        <div
          v-for="suggestion in suggestions"
          :key="suggestion.value"
          @click="applySuggestion(suggestion)"
          class="suggestion-item"
        >
          <span class="suggestion-type">{{ suggestion.type }}</span>
          <span class="suggestion-label">{{ suggestion.label }}</span>
        </div>
      </div>
    </div>

    <div class="search-content">
      <!-- 左侧筛选器 (Facets) -->
      <div class="facets-sidebar">
        <h3>筛选器</h3>
        
        <!-- 文档类型 -->
        <div class="facet-group">
          <h4>📄 文档类型</h4>
          <div class="facet-options">
            <label v-for="item in facets.document_type" :key="item.document_type" class="facet-option">
              <input
                type="checkbox"
                :value="item.document_type"
                v-model="selectedFilters.document_type"
                @change="applyFilters"
              />
              <span>{{ item.document_type }} ({{ item.count }})</span>
            </label>
          </div>
        </div>

        <!-- 文件格式 -->
        <div class="facet-group">
          <h4>📁 文件格式</h4>
          <div class="facet-options">
            <label v-for="item in facets.file_format" :key="item.file_format" class="facet-option">
              <input
                type="checkbox"
                :value="item.file_format"
                v-model="selectedFilters.file_format"
                @change="applyFilters"
              />
              <span>{{ item.file_format }} ({{ item.count }})</span>
            </label>
          </div>
        </div>

        <!-- 物种 -->
        <div class="facet-group" v-if="facets.organism && facets.organism.length > 0">
          <h4>🧬 物种</h4>
          <div class="facet-options">
            <label v-for="item in facets.organism" :key="item.organism" class="facet-option">
              <input
                type="checkbox"
                :value="item.organism"
                v-model="selectedFilters.organism"
                @change="applyFilters"
              />
              <span>{{ item.organism }} ({{ item.count }})</span>
            </label>
          </div>
        </div>

        <!-- 项目 -->
        <div class="facet-group">
          <h4>📊 项目</h4>
          <div class="facet-options">
            <label v-for="item in facets.project" :key="item.project" class="facet-option">
              <input
                type="checkbox"
                :value="item.project"
                v-model="selectedFilters.project"
                @change="applyFilters"
              />
              <span>{{ item.project }} ({{ item.count }})</span>
            </label>
          </div>
        </div>

        <!-- 实验类型 -->
        <div class="facet-group" v-if="facets.experiment_type && facets.experiment_type.length > 0">
          <h4>🔬 实验类型</h4>
          <div class="facet-options">
            <label v-for="item in facets.experiment_type" :key="item.experiment_type" class="facet-option">
              <input
                type="checkbox"
                :value="item.experiment_type"
                v-model="selectedFilters.experiment_type"
                @change="applyFilters"
              />
              <span>{{ item.experiment_type }} ({{ item.count }})</span>
            </label>
          </div>
        </div>

        <!-- 访问级别 -->
        <div class="facet-group">
          <h4>🔒 访问级别</h4>
          <div class="facet-options">
            <label v-for="item in facets.access_level" :key="item.access_level" class="facet-option">
              <input
                type="checkbox"
                :value="item.access_level"
                v-model="selectedFilters.access_level"
                @change="applyFilters"
              />
              <span>{{ item.access_level }} ({{ item.count }})</span>
            </label>
          </div>
        </div>

        <!-- 清除筛选器 -->
        <button @click="clearFilters" class="clear-filters-btn">
          清除所有筛选器
        </button>
      </div>

      <!-- 右侧搜索结果 -->
      <div class="search-results">
        <!-- 搜索信息 -->
        <div class="search-info" v-if="searchPerformed">
          <div class="results-summary">
            <span v-if="searchResults.pagination">
              找到 {{ searchResults.pagination.total_count }} 个文件
              (第 {{ searchResults.pagination.page }} 页，共 {{ searchResults.pagination.total_pages }} 页)
            </span>
            <span v-else>搜索中...</span>
          </div>
          
          <!-- 排序选项 -->
          <div class="sort-options">
            <label>排序:</label>
            <select v-model="sortBy" @change="applyFilters">
              <option value="uploaded_at">上传时间</option>
              <option value="title">标题</option>
              <option value="file_size">文件大小</option>
              <option value="project">项目</option>
            </select>
            <select v-model="sortOrder" @change="applyFilters">
              <option value="desc">降序</option>
              <option value="asc">升序</option>
            </select>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="isSearching" class="loading-state">
          <div class="loading-spinner"></div>
          <p>搜索中...</p>
        </div>

        <!-- 搜索结果列表 -->
        <div v-else-if="searchResults.results && searchResults.results.length > 0" class="results-list">
          <div
            v-for="file in searchResults.results"
            :key="file.id"
            class="result-item"
            @click="showFilePreview(file)"
          >
            <div class="file-icon">
              {{ getFileIcon(file.file_format) }}
            </div>
            
            <div class="file-info">
              <h3 class="file-title">{{ file.title || file.original_filename }}</h3>
              <p class="file-meta">
                <span class="project">📊 {{ file.project }}</span>
                <span class="format">📁 {{ file.file_format }}</span>
                <span class="size">💾 {{ formatFileSize(file.file_size) }}</span>
                <span class="date">📅 {{ formatDate(file.uploaded_at) }}</span>
              </p>
              <p v-if="file.organism" class="organism">🧬 {{ file.organism }}</p>
              <p v-if="file.description" class="description">{{ file.description }}</p>
              <div v-if="file.tags_list && file.tags_list.length > 0" class="tags">
                <span v-for="tag in file.tags_list" :key="tag" class="tag">{{ tag }}</span>
              </div>
            </div>
            
            <div class="file-actions">
              <button @click.stop="downloadFile(file)" class="action-btn download-btn">
                下载
              </button>
              <button @click.stop="showFilePreview(file)" class="action-btn preview-btn">
                预览
              </button>
            </div>
          </div>
        </div>

        <!-- 无结果状态 -->
        <div v-else-if="searchPerformed && !isSearching" class="no-results">
          <div class="no-results-icon">🔍</div>
          <h3>未找到匹配的文件</h3>
          <p>尝试调整搜索关键词或筛选条件</p>
          <div class="search-tips">
            <h4>搜索技巧:</h4>
            <ul>
              <li>使用 <code>project:项目名</code> 搜索特定项目</li>
              <li>使用 <code>organism:物种名</code> 搜索特定物种</li>
              <li>使用 <code>format:FASTQ</code> 搜索特定格式</li>
              <li>组合使用: <code>human RNA-seq project:MyLab</code></li>
            </ul>
          </div>
        </div>

        <!-- 初始状态 -->
        <div v-else class="initial-state">
          <div class="welcome-icon">🗂️</div>
          <h3>开始搜索您的文件</h3>
          <p>在上方输入关键词，或使用左侧筛选器浏览文件</p>
        </div>

        <!-- 分页 -->
        <div v-if="searchResults.pagination && searchResults.pagination.total_pages > 1" class="pagination">
          <button
            @click="goToPage(searchResults.pagination.page - 1)"
            :disabled="!searchResults.pagination.has_previous"
            class="page-btn"
          >
            上一页
          </button>
          
          <span class="page-info">
            第 {{ searchResults.pagination.page }} 页 / 共 {{ searchResults.pagination.total_pages }} 页
          </span>
          
          <button
            @click="goToPage(searchResults.pagination.page + 1)"
            :disabled="!searchResults.pagination.has_next"
            class="page-btn"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 文件预览模态框 -->
    <FilePreviewModal
      v-if="showPreviewModal"
      :file="selectedFile"
      @close="closePreview"
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useFilesStore } from '../stores/files'
import FilePreviewModal from '../components/FilePreviewModal.vue'

export default {
  name: 'FileSearch',
  components: {
    FilePreviewModal
  },
  setup() {
    const router = useRouter()
    const filesStore = useFilesStore()
    
    // 响应式数据
    const searchQuery = ref('')
    const isSearching = ref(false)
    const searchPerformed = ref(false)
    const suggestions = ref([])
    const searchResults = reactive({
      results: [],
      pagination: null,
      facets: {},
      query_info: {}
    })
    
    // 筛选器状态
    const facets = reactive({
      document_type: [],
      file_format: [],
      organism: [],
      project: [],
      experiment_type: [],
      access_level: []
    })
    
    const selectedFilters = reactive({
      document_type: [],
      file_format: [],
      organism: [],
      project: [],
      experiment_type: [],
      access_level: []
    })
    
    // 排序选项
    const sortBy = ref('uploaded_at')
    const sortOrder = ref('desc')
    
    // 预览相关
    const showPreviewModal = ref(false)
    const selectedFile = ref(null)
    
    // 分页
    const currentPage = ref(1)
    
    // 搜索建议防抖
    let suggestionTimeout = null
    
    // 方法
    const performSearch = async () => {
      if (isSearching.value) return
      
      isSearching.value = true
      searchPerformed.value = true
      
      try {
        const params = {
          q: searchQuery.value,
          page: currentPage.value,
          sort_by: sortBy.value,
          sort_order: sortOrder.value,
          ...getFilterParams()
        }
        
        const response = await filesStore.searchFiles(params)
        
        Object.assign(searchResults, response)
        Object.assign(facets, response.facets || {})
        
      } catch (error) {
        console.error('搜索失败:', error)
        // 可以添加错误提示
      } finally {
        isSearching.value = false
      }
    }
    
    const onSearchInput = () => {
      // 清除之前的定时器
      if (suggestionTimeout) {
        clearTimeout(suggestionTimeout)
      }
      
      // 设置新的定时器
      suggestionTimeout = setTimeout(async () => {
        if (searchQuery.value.length >= 2) {
          try {
            const response = await filesStore.getSearchSuggestions(searchQuery.value)
            suggestions.value = response.suggestions || []
          } catch (error) {
            console.error('获取搜索建议失败:', error)
          }
        } else {
          suggestions.value = []
        }
      }, 300)
    }
    
    const applySuggestion = (suggestion) => {
      searchQuery.value = suggestion.value
      suggestions.value = []
      performSearch()
    }
    
    const applyFilters = () => {
      currentPage.value = 1
      performSearch()
    }
    
    const clearFilters = () => {
      Object.keys(selectedFilters).forEach(key => {
        selectedFilters[key] = []
      })
      applyFilters()
    }
    
    const getFilterParams = () => {
      const params = {}
      Object.keys(selectedFilters).forEach(key => {
        if (selectedFilters[key].length > 0) {
          params[key] = selectedFilters[key].join(',')
        }
      })
      return params
    }
    
    const goToPage = (page) => {
      currentPage.value = page
      performSearch()
    }
    
    const showFilePreview = (file) => {
      selectedFile.value = file
      showPreviewModal.value = true
    }
    
    const closePreview = () => {
      showPreviewModal.value = false
      selectedFile.value = null
    }
    
    const downloadFile = async (file) => {
      try {
        await filesStore.downloadFile(file.id, file.original_filename)
      } catch (error) {
        console.error('下载失败:', error)
      }
    }
    
    const getFileIcon = (format) => {
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
      if (!bytes) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    // 初始化加载筛选器数据
    const loadFacets = async () => {
      try {
        const response = await filesStore.getFacets()
        Object.assign(facets, response.facets || {})
      } catch (error) {
        console.error('加载筛选器数据失败:', error)
      }
    }
    
    // 生命周期
    onMounted(() => {
      loadFacets()
    })
    
    return {
      searchQuery,
      isSearching,
      searchPerformed,
      suggestions,
      searchResults,
      facets,
      selectedFilters,
      sortBy,
      sortOrder,
      showPreviewModal,
      selectedFile,
      currentPage,
      performSearch,
      onSearchInput,
      applySuggestion,
      applyFilters,
      clearFilters,
      goToPage,
      showFilePreview,
      closePreview,
      downloadFile,
      getFileIcon,
      formatFileSize,
      formatDate
    }
  }
}
</script>

<style scoped>
.file-search-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem;
  background: var(--waves-surface-primary);
  min-height: 100vh;
}

.search-header {
  text-align: center;
  margin-bottom: 2rem;
}

.search-header h1 {
  font-size: 2.5rem;
  color: var(--waves-text-primary);
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.search-subtitle {
  color: var(--waves-text-secondary);
  font-size: 1.125rem;
  line-height: 1.6;
}

.search-box-container {
  position: relative;
  margin-bottom: 2rem;
}

.search-box {
  display: flex;
  max-width: 800px;
  margin: 0 auto;
  box-shadow: var(--waves-shadow-lg);
  border-radius: var(--waves-radius-xl);
  overflow: hidden;
  border: 1px solid var(--waves-border-light);
  background: var(--waves-surface-secondary);
}

.search-input {
  flex: 1;
  padding: 1rem 1.5rem;
  border: none;
  font-size: 1.125rem;
  outline: none;
  background: transparent;
  color: var(--waves-text-primary);
}

.search-input::placeholder {
  color: var(--waves-text-secondary);
}

.search-button {
  padding: 1rem 2rem;
  background: var(--waves-primary-600);
  color: white;
  border: none;
  font-size: 1.125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.search-button:hover {
  background: var(--waves-primary-700);
  transform: translateY(-1px);
}

.search-suggestions {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 800px;
  background: var(--waves-surface-secondary);
  border: 1px solid var(--waves-border-light);
  border-top: none;
  border-radius: 0 0 var(--waves-radius-xl) var(--waves-radius-xl);
  box-shadow: var(--waves-shadow-lg);
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.suggestion-item {
  padding: 0.75rem 1.5rem;
  cursor: pointer;
  border-bottom: 1px solid var(--waves-border-light);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  transition: all 0.3s ease;
}

.suggestion-item:hover {
  background: var(--waves-primary-50);
  color: var(--waves-primary-700);
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-type {
  background: var(--waves-primary-100);
  color: var(--waves-primary-700);
  padding: 0.25rem 0.75rem;
  border-radius: var(--waves-radius-full);
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.search-content {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 2rem;
}

.facets-sidebar {
  background: var(--waves-surface-secondary);
  padding: 1.5rem;
  border-radius: var(--waves-radius-xl);
  height: fit-content;
  position: sticky;
  top: 1.5rem;
  border: 1px solid var(--waves-border-light);
  box-shadow: var(--waves-shadow-md);
}

.facets-sidebar h3 {
  margin-top: 0;
  color: var(--waves-text-primary);
  border-bottom: 2px solid var(--waves-primary-500);
  padding-bottom: 0.75rem;
  font-weight: 600;
  font-size: 1.125rem;
}

.facet-group {
  margin-bottom: 1.75rem;
}

.facet-group h4 {
  margin-bottom: 0.75rem;
  color: var(--waves-text-primary);
  font-size: 1rem;
  font-weight: 500;
}

.facet-options {
  max-height: 200px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.facet-options::-webkit-scrollbar {
  width: 6px;
}

.facet-options::-webkit-scrollbar-track {
  background: var(--waves-surface-primary);
  border-radius: var(--waves-radius-full);
}

.facet-options::-webkit-scrollbar-thumb {
  background: var(--waves-border-medium);
  border-radius: var(--waves-radius-full);
}

.facet-options::-webkit-scrollbar-thumb:hover {
  background: var(--waves-border-dark);
}

.facet-option {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  padding: 0.25rem 0;
  transition: color 0.3s ease;
}

.facet-option:hover {
  color: var(--waves-primary-600);
}

.facet-option input {
  margin-right: 0.75rem;
  accent-color: var(--waves-primary-500);
}

.clear-filters-btn {
  width: 100%;
  padding: 0.75rem 1rem;
  background: var(--waves-danger-500);
  color: white;
  border: none;
  border-radius: var(--waves-radius-lg);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.clear-filters-btn:hover {
  background: var(--waves-danger-600);
  transform: translateY(-1px);
  box-shadow: var(--waves-shadow-md);
}

.search-results {
  min-height: 400px;
}

.search-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding: 1rem 1.5rem;
  background: var(--waves-surface-secondary);
  border-radius: var(--waves-radius-xl);
  border: 1px solid var(--waves-border-light);
  box-shadow: var(--waves-shadow-sm);
}

.sort-options {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sort-options label {
  color: var(--waves-text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
}

.sort-options select {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--waves-border-light);
  border-radius: var(--waves-radius-lg);
  background: var(--waves-surface-primary);
  color: var(--waves-text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sort-options select:focus {
  outline: none;
  border-color: var(--waves-primary-500);
  box-shadow: 0 0 0 3px var(--waves-primary-100);
}

.loading-state {
  text-align: center;
  padding: 4rem 1.5rem;
  color: var(--waves-text-secondary);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--waves-border-light);
  border-top: 4px solid var(--waves-primary-500);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1.5rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1.5rem;
  background: var(--waves-surface-secondary);
  border: 1px solid var(--waves-border-light);
  border-radius: var(--waves-radius-xl);
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: var(--waves-shadow-sm);
}

.result-item:hover {
  box-shadow: var(--waves-shadow-lg);
  transform: translateY(-2px);
  border-color: var(--waves-primary-200);
}

.file-icon {
  font-size: 2.5rem;
  flex-shrink: 0;
  color: var(--waves-primary-500);
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-title {
  margin: 0 0 0.75rem 0;
  color: var(--waves-text-primary);
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.4;
}

.file-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.5rem;
  color: var(--waves-text-secondary);
  font-size: 0.875rem;
}

.file-meta > span {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.organism, .description {
  margin: 0.375rem 0;
  color: var(--waves-text-primary);
  font-size: 0.875rem;
  line-height: 1.5;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.tag {
  background: var(--waves-primary-100);
  color: var(--waves-primary-700);
  padding: 0.25rem 0.75rem;
  border-radius: var(--waves-radius-full);
  font-size: 0.75rem;
  font-weight: 500;
}

.file-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex-shrink: 0;
}

.action-btn {
  padding: 0.75rem 1.25rem;
  border: none;
  border-radius: var(--waves-radius-lg);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  min-width: 120px;
}

.download-btn {
  background: #28a745;
  color: #ffffff !important;
  font-weight: 600;
}

.download-btn:hover {
  background: #218838;
  color: #ffffff !important;
  transform: translateY(-1px);
  box-shadow: var(--waves-shadow-md);
}

.preview-btn {
  background: #17a2b8;
  color: #ffffff !important;
  font-weight: 600;
}

.preview-btn:hover {
  background: #138496;
  color: #ffffff !important;
  transform: translateY(-1px);
  box-shadow: var(--waves-shadow-md);
}

.no-results, .initial-state {
  text-align: center;
  padding: 4rem 1.5rem;
  color: var(--waves-text-secondary);
  background: var(--waves-surface-secondary);
  border-radius: var(--waves-radius-xl);
  border: 1px solid var(--waves-border-light);
  margin: 2rem 0;
}

.no-results-icon, .welcome-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  color: var(--waves-primary-400);
}

.search-tips {
  margin-top: 2rem;
  text-align: left;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
  background: var(--waves-surface-primary);
  padding: 1.5rem;
  border-radius: var(--waves-radius-lg);
  border: 1px solid var(--waves-border-light);
}

.search-tips h4 {
  color: var(--waves-text-primary);
  margin-bottom: 1rem;
  font-weight: 600;
}

.search-tips ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.search-tips li {
  margin-bottom: 0.75rem;
  padding-left: 2rem;
  position: relative;
  line-height: 1.5;
}

.search-tips li:before {
  content: "💡";
  position: absolute;
  left: 0;
  top: 0;
}

.search-tips code {
  background: var(--waves-primary-50);
  color: var(--waves-primary-700);
  padding: 0.25rem 0.5rem;
  border-radius: var(--waves-radius-sm);
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  font-size: 0.875em;
  font-weight: 500;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  margin-top: 2rem;
  padding: 1.5rem;
  background: var(--waves-surface-secondary);
  border-radius: var(--waves-radius-xl);
  border: 1px solid var(--waves-border-light);
}

.page-btn {
  padding: 0.75rem 1.5rem;
  background: var(--waves-primary-500);
  color: white;
  border: none;
  border-radius: var(--waves-radius-lg);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.page-btn:hover:not(:disabled) {
  background: var(--waves-primary-600);
  transform: translateY(-1px);
  box-shadow: var(--waves-shadow-md);
}

.page-btn:disabled {
  background: var(--waves-gray-400);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.page-info {
  color: var(--waves-text-secondary);
  font-weight: 500;
  font-size: 0.875rem;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .search-content {
    grid-template-columns: 280px 1fr;
    gap: 1.5rem;
  }
  
  .facets-sidebar {
    padding: 1rem;
  }
}

@media (max-width: 768px) {
  .file-search-container {
    padding: 1rem;
  }
  
  .search-content {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .facets-sidebar {
    position: static;
    order: 2;
  }
  
  .search-results {
    order: 1;
  }
  
  .search-info {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .result-item {
    flex-direction: column;
    gap: 1rem;
  }
  
  .file-actions {
    flex-direction: row;
    justify-content: center;
    gap: 0.75rem;
  }
  
  .action-btn {
    min-width: auto;
    flex: 1;
  }
  
  .pagination {
    flex-direction: column;
    gap: 1rem;
  }
}

@media (max-width: 480px) {
  .search-header h1 {
    font-size: 2rem;
  }
  
  .search-box {
    flex-direction: column;
  }
  
  .search-button {
    border-radius: 0 0 var(--waves-radius-xl) var(--waves-radius-xl);
  }
  
  .file-actions {
    flex-direction: column;
  }
}
</style>