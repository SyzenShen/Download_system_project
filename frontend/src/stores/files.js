import { defineStore } from 'pinia'
import axios from 'axios'

export const useFilesStore = defineStore('files', {
  state: () => ({
    files: [],
    folders: [],
    currentFolder: null,
    breadcrumb: [],
    isLoading: false,
    error: null,
    uploadProgress: 0,
    downloadProgress: {},
    // 上传控制
    uploadController: null,
    uploadPauseRequested: false,
    uploadCancelRequested: false,
    uploadPaused: false,
    uploadSessionId: null,
    uploadChunkSize: 2 * 1024 * 1024,
    uploadUploadedSize: 0,
    uploadFileRef: null,
    uploadMethodRef: 'Vue Frontend',
    currentFolderId: null, // 当前所在文件夹ID
    // 下载控制（按文件ID）
    downloadControllers: {},
    downloadPauseRequested: {},
    downloadCancelRequested: {},
    downloadPaused: {},
    downloadActive: {},
    downloadHandles: {},
    // 新增：界面控制
    viewMode: 'list', // 'list' 或 'grid'
    showUploadDialog: false,
    showNewFolderDialog: false,
    loadingOverlayVisible: false,
    loadingOverlayMessage: '请稍候...',
    lastPublishedCellxgeneFile: null
  }),

  getters: {
    // 当前文件夹中的文件
    currentFiles: (state) => {
      return state.files.filter(file => {
        if (state.currentFolderId === null) {
          return !file.parent_folder
        }
        return file.parent_folder === state.currentFolderId
      })
    },
    
    // 当前文件夹中的子文件夹
    currentFolders: (state) => {
      return state.folders.filter(folder => {
        if (state.currentFolderId === null) {
          return !folder.parent
        }
        return folder.parent === state.currentFolderId
      })
    },
    
    // 根级文件夹
    rootFolders: (state) => {
      return state.folders.filter(folder => !folder.parent)
    }
  },

  actions: {
    async fetchFiles(folderId = null) {
      this.isLoading = true
      this.error = null
      
      try {
        const url = folderId ? `/api/files/?folder_id=${folderId}` : '/api/files/'
        const response = await axios.get(url)
        
        // 更新状态
        this.files = response.data.files || []
        this.folders = response.data.folders || []
        this.currentFolder = response.data.current_folder || null
        this.currentFolderId = this.currentFolder ? this.currentFolder.id : null
        
        // 获取面包屑导航
        if (folderId) {
          await this.fetchBreadcrumb(folderId)
        } else {
          this.breadcrumb = []
        }
      } catch (error) {
        this.error = error.response?.data?.message || '获取文件列表失败'
        console.error('Fetch files error:', error)
      } finally {
        this.isLoading = false
      }
    },

    async uploadFile(file, uploadMethod = 'Vue Frontend', parentFolderId = null) {
      // 启用分片上传以支持真正暂停/继续
      this.isLoading = true
      this.error = null
      this.uploadProgress = 0
      this.uploadPauseRequested = false
      this.uploadCancelRequested = false
      this.uploadPaused = false
      this.uploadFileRef = file
      this.uploadMethodRef = uploadMethod
      this.uploadUploadedSize = 0
      this.uploadSessionId = null
      // 控制器用于中断 fetch
      this.uploadController = new AbortController()

      const token = localStorage.getItem('token')
      const commonAuthHeader = token ? { Authorization: `Token ${token}` } : {}

      try {
        // 初始化分片会话
        const initBody = { 
          filename: file.name, 
          total_size: file.size, 
          chunk_size: this.uploadChunkSize 
        }
        if (parentFolderId) {
          initBody.parent_folder_id = parentFolderId
        }
        
        const initRes = await fetch('/api/files/chunked/init/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...commonAuthHeader },
          body: JSON.stringify(initBody),
          signal: this.uploadController.signal
        })
        if (!initRes.ok) {
          const txt = await initRes.text().catch(() => '')
          throw new Error(txt || '初始化分片上传失败')
        }
        const initData = await initRes.json()
        this.uploadSessionId = initData.session_id
        this.uploadChunkSize = initData.chunk_size || this.uploadChunkSize

        // 执行分片上传循环
        const doChunkLoop = async () => {
          while (this.uploadUploadedSize < file.size) {
            if (this.uploadPauseRequested || this.uploadCancelRequested) {
              // 模拟 AbortError，进入 catch 分支
              const err = new DOMException('aborted', 'AbortError')
              throw err
            }
            const start = this.uploadUploadedSize
            const end = Math.min(start + this.uploadChunkSize, file.size)
            const blob = file.slice(start, end)
            const ab = await blob.arrayBuffer()
            const headers = {
              'Content-Range': `bytes ${start}-${end - 1}/${file.size}`,
              ...commonAuthHeader
            }
            const chunkRes = await fetch(`/api/files/chunked/${this.uploadSessionId}/chunk/`, {
              method: 'PUT',
              headers,
              body: ab,
              signal: this.uploadController.signal
            })
            if (!chunkRes.ok) {
              const txt = await chunkRes.text().catch(() => '')
              throw new Error(txt || '分片上传失败')
            }
            this.uploadUploadedSize = end
            this.uploadProgress = Math.round((this.uploadUploadedSize * 100) / file.size)
          }
        }

        await doChunkLoop()

        // 完成上传
        const completeRes = await fetch(`/api/files/chunked/${this.uploadSessionId}/complete/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...commonAuthHeader },
          body: JSON.stringify({}),
          signal: this.uploadController.signal
        })
        if (!completeRes.ok) {
          const txt = await completeRes.text().catch(() => '')
          throw new Error(txt || '完成上传失败')
        }

        // 刷新文件列表，保持在当前文件夹
        await this.fetchFiles(this.currentFolderId)

        // 清理并返回成功
        this.isLoading = false
        this.uploadController = null
        this.uploadPauseRequested = false
        this.uploadCancelRequested = false
        this.uploadPaused = false
        this.uploadSessionId = null
        this.uploadUploadedSize = 0
        this.uploadProgress = 0
        return { success: true, message: '文件上传成功' }
      } catch (error) {
        const aborted = this.uploadPauseRequested || this.uploadCancelRequested || error?.name === 'AbortError' || error?.code === 'ERR_CANCELED'
        if (aborted) {
          if (this.uploadPauseRequested) {
            this.uploadPaused = true
            this.isLoading = false
            this.uploadController = null
            // 保留 sessionId 和已上传大小，便于继续
            return { success: false, error: '上传已暂停' }
          }
          if (this.uploadCancelRequested) {
            // 取消后通知后端清理临时文件
            try {
              await fetch(`/api/files/chunked/${this.uploadSessionId}/cancel/`, { method: 'POST', headers: { ...commonAuthHeader } })
            } catch (_) {}
            this.isLoading = false
            this.uploadController = null
            this.uploadPaused = false
            this.uploadSessionId = null
            this.uploadUploadedSize = 0
            this.uploadProgress = 0
            this.uploadPauseRequested = false
            this.uploadCancelRequested = false
            return { success: false, error: '上传已取消' }
          }
        }
        const msg = error?.message || error?.response?.data?.message || '文件上传失败'
        this.error = msg
        // 发生错误时不清理状态，便于用户选择取消或重试
        this.isLoading = false
        this.uploadController = null
        return { success: false, error: msg }
      }
    },

    pauseUpload() {
      if (this.uploadController) {
        this.uploadPauseRequested = true
        this.uploadPaused = true
        this.uploadController.abort()
      }
    },

    cancelUpload() {
      if (this.uploadController) {
        this.uploadCancelRequested = true
        this.uploadController.abort()
      }
      this.uploadPaused = false
    },

    async resumeUpload() {
      // 使用现有会话从断点继续
      if (!this.uploadFileRef || !this.uploadSessionId) {
        // 若无会话，回退为重新上传
        if (this.uploadFileRef) {
          return await this.uploadFile(this.uploadFileRef, this.uploadMethodRef)
        }
        return { success: false, error: '没有可恢复的上传会话' }
      }
      this.error = null
      this.isLoading = true
      this.uploadPaused = false
      this.uploadPauseRequested = false
      this.uploadCancelRequested = false
      this.uploadController = new AbortController()

      const file = this.uploadFileRef
      const token = localStorage.getItem('token')
      const commonAuthHeader = token ? { Authorization: `Token ${token}` } : {}

      try {
        while (this.uploadUploadedSize < file.size) {
          if (this.uploadPauseRequested || this.uploadCancelRequested) {
            const err = new DOMException('aborted', 'AbortError')
            throw err
          }
          const start = this.uploadUploadedSize
          const end = Math.min(start + this.uploadChunkSize, file.size)
          const blob = file.slice(start, end)
          const ab = await blob.arrayBuffer()
          const headers = {
            'Content-Range': `bytes ${start}-${end - 1}/${file.size}`,
            ...commonAuthHeader
          }
          const chunkRes = await fetch(`/api/files/chunked/${this.uploadSessionId}/chunk/`, {
            method: 'PUT',
            headers,
            body: ab,
            signal: this.uploadController.signal
          })
          if (!chunkRes.ok) {
            const txt = await chunkRes.text().catch(() => '')
            throw new Error(txt || '分片上传失败')
          }
          this.uploadUploadedSize = end
          this.uploadProgress = Math.round((this.uploadUploadedSize * 100) / file.size)
        }

        const completeRes = await fetch(`/api/files/chunked/${this.uploadSessionId}/complete/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...commonAuthHeader },
          body: JSON.stringify({}),
          signal: this.uploadController.signal
        })
        if (!completeRes.ok) {
          const txt = await completeRes.text().catch(() => '')
          throw new Error(txt || '完成上传失败')
        }

        await this.fetchFiles()

        this.isLoading = false
        this.uploadController = null
        this.uploadPauseRequested = false
        this.uploadCancelRequested = false
        this.uploadPaused = false
        this.uploadSessionId = null
        this.uploadUploadedSize = 0
        this.uploadProgress = 0
        return { success: true, message: '文件上传成功' }
      } catch (error) {
        const aborted = this.uploadPauseRequested || this.uploadCancelRequested || error?.name === 'AbortError' || error?.code === 'ERR_CANCELED'
        if (aborted) {
          if (this.uploadPauseRequested) {
            this.uploadPaused = true
            this.isLoading = false
            this.uploadController = null
            return { success: false, error: '上传已暂停' }
          }
          if (this.uploadCancelRequested) {
            try {
              await fetch(`/api/files/chunked/${this.uploadSessionId}/cancel/`, { method: 'POST', headers: { ...commonAuthHeader } })
            } catch (_) {}
            this.isLoading = false
            this.uploadController = null
            this.uploadPaused = false
            this.uploadSessionId = null
            this.uploadUploadedSize = 0
            this.uploadProgress = 0
            this.uploadPauseRequested = false
            this.uploadCancelRequested = false
            return { success: false, error: '上传已取消' }
          }
        }
        const msg = error?.message || error?.response?.data?.message || '文件上传失败'
        this.error = msg
        this.isLoading = false
        this.uploadController = null
        return { success: false, error: msg }
      }
    },

    async deleteFile(fileId) {
      try {
        // 显式附加鉴权头，避免某些环境下axios默认头丢失
        const token = localStorage.getItem('token')
        const headers = token ? { Authorization: `Token ${token}` } : {}
        
        await axios.delete(`/api/files/${fileId}/delete/`, { headers })
        
        // 从本地状态中移除文件
        this.files = this.files.filter(file => file.id !== fileId)
        
        return { success: true, message: '文件删除成功' }
      } catch (error) {
        const message = error.response?.data?.message 
          || error.response?.data?.error 
          || error.response?.data?.detail 
          || '文件删除失败'
        // 若后端返回404，提示更友好
        if (error.response?.status === 404) {
          this.error = '文件不存在或无权限删除'
          return { success: false, error: this.error }
        }
        this.error = message
        return { success: false, error: message }
      }
    },

    // 发布到 Cellxgene：将指定文件复制到后端配置的数据目录
    async publishToCellxgene(fileId) {
      this.error = null
      try {
        const token = localStorage.getItem('token')
        const headers = token ? { Authorization: `Token ${token}` } : {}
        const res = await axios.post(`/api/files/${fileId}/publish-cellxgene/`, {}, { headers })
        const payload = res.data || {}
        const cellxgeneStatus = payload?.cellxgene?.status
        if (cellxgeneStatus === 'error') {
          const errMsg = payload?.cellxgene?.message || payload?.message || '发布到 Cellxgene 失败'
          this.showErrorNotification(errMsg)
          return { success: false, data: payload, error: errMsg }
        }
        const successMsg = payload?.message || '已发布到 Cellxgene 数据目录'
        this.showNotification(successMsg)
        const publishedFile = payload?.published_file
        if (publishedFile) {
          this.lastPublishedCellxgeneFile = publishedFile
        }
        return { success: true, data: payload }
      } catch (error) {
        const msg = error?.response?.data?.message || '发布到 Cellxgene 失败'
        this.showErrorNotification(msg)
        return { success: false, error: msg }
      }
    },

    // 文件夹相关方法
    async createFolder(name, parentFolderId = null) {
      try {
        const token = localStorage.getItem('token')
        const headers = token ? { Authorization: `Token ${token}` } : {}
        
        const data = { name }
        if (parentFolderId) {
          data.parent = parentFolderId
        }
        
        const response = await axios.post('/api/files/folders/', data, { headers })
        
        // 添加到本地状态
        this.folders.push(response.data)
        
        return { success: true, folder: response.data }
      } catch (error) {
        const message = error.response?.data?.message 
          || error.response?.data?.error 
          || error.response?.data?.detail 
          || '创建文件夹失败'
        this.error = message
        return { success: false, error: message }
      }
    },

    async deleteFolder(folderId) {
      try {
        const token = localStorage.getItem('token')
        const headers = token ? { Authorization: `Token ${token}` } : {}
        
        await axios.delete(`/api/files/folders/${folderId}/`, { headers })
        
        // 从本地状态中移除文件夹
        this.folders = this.folders.filter(folder => folder.id !== folderId)
        
        return { success: true, message: '文件夹删除成功' }
      } catch (error) {
        const message = error.response?.data?.message 
          || error.response?.data?.error 
          || error.response?.data?.detail 
          || '删除文件夹失败'
        this.error = message
        return { success: false, error: message }
      }
    },

    async fetchBreadcrumb(folderId) {
      try {
        const token = localStorage.getItem('token')
        const headers = token ? { Authorization: `Token ${token}` } : {}
        
        const response = await axios.get(`/api/files/folders/${folderId}/breadcrumb/`, { headers })
        this.breadcrumb = response.data
      } catch (error) {
        console.error('获取面包屑导航失败:', error)
        this.breadcrumb = []
      }
    },

    // 导航到指定文件夹
    async navigateToFolder(folderId) {
      await this.fetchFiles(folderId)
    },

    // 返回上级目录
    async navigateUp() {
      if (this.currentFolder && this.currentFolder.parent) {
        await this.fetchFiles(this.currentFolder.parent)
      } else {
        await this.fetchFiles(null) // 返回根目录
      }
    },

    async downloadFile(fileId, filename, fileSize, opts = {}) {
      const maxRetries = opts.maxRetries || 3
      const retryDelay = opts.retryDelay || 1000
      let retryCount = opts.retryCount || 0
      
      // 显示下载开始提示（仅在首次尝试时显示）
      if (retryCount === 0 && !opts.useExistingHandle) {
        this.showDownloadNotification(`开始下载: ${filename}`)
      }
      
      // 如果浏览器支持文件系统访问API，则使用流式+Range断点续传
      const supportsFS = typeof window.showSaveFilePicker === 'function'
      const useExistingHandle = !!opts.useExistingHandle
      if (!useExistingHandle) {
        this.downloadProgress[fileId] = 0
      }
      this.downloadPauseRequested[fileId] = false
      this.downloadCancelRequested[fileId] = false
      this.downloadPaused[fileId] = false
      // 每次启动下载都创建新的控制器
      const controller = new AbortController()
      this.downloadControllers[fileId] = controller

      const cleanup = (mode) => {
        // 通用清理：控制器与标记
        delete this.downloadControllers[fileId]
        delete this.downloadPauseRequested[fileId]
        delete this.downloadCancelRequested[fileId]
        if (mode === 'success') {
          delete this.downloadProgress[fileId]
          delete this.downloadPaused[fileId]
          delete this.downloadActive[fileId]
        } else if (mode === 'cancel') {
          delete this.downloadProgress[fileId]
          delete this.downloadPaused[fileId]
          delete this.downloadActive[fileId]
        } else if (mode === 'pause') {
          // 保留进度与 active，用于显示“继续”与进度条
          this.downloadPaused[fileId] = true
        } else {
          // 其它错误，尽量复位
          delete this.downloadProgress[fileId]
          delete this.downloadPaused[fileId]
          delete this.downloadActive[fileId]
        }
      }

      // 在 try/catch 外声明，便于在取消时调用 abort()
      let writable = null
      let fileHandle = null
      try {
        const ONE_GB = 1 * 1024 * 1024 * 1024
        const shouldResume = (fileSize || 0) >= ONE_GB
        if (supportsFS) {
          // 复用内存句柄或全局窗口句柄，避免 HMR/刷新导致丢失
          const globalHandles = (window.__downloadHandles = window.__downloadHandles || {})
          const cachedHandle = useExistingHandle ? (this.downloadHandles[fileId] || globalHandles[fileId]) : null
          if (cachedHandle) {
            fileHandle = cachedHandle
            try {
              // 先查询权限，已授予则不弹窗
              const q = await fileHandle.queryPermission?.({ mode: 'readwrite' })
              if (q !== 'granted') {
                await fileHandle.requestPermission?.({ mode: 'readwrite' })
              }
            } catch (_) {}
          } else {
            fileHandle = await window.showSaveFilePicker({ suggestedName: filename })
            this.downloadHandles[fileId] = fileHandle
            globalHandles[fileId] = fileHandle
          }
          // 用户选择了文件名和保存位置后，才标记为下载中
          this.downloadActive[fileId] = true
          let existingSize = 0
          try {
            const existingFile = await fileHandle.getFile()
            existingSize = existingFile.size || 0
          } catch (e) {
            existingSize = 0
          }

          // 在续传场景下，先用已存在大小与总大小计算一个初始进度
          if (useExistingHandle && Number.isFinite(existingSize) && Number.isFinite(fileSize) && fileSize > 0) {
            this.downloadProgress[fileId] = Math.min(Math.round((existingSize * 100) / fileSize), 99)
          }

          const headers = {}
          if (shouldResume && existingSize > 0 && Number.isFinite(existingSize)) {
            headers['Range'] = `bytes=${existingSize}-`
          }

          // 附加鉴权头（Token），与 axios 保持一致
          const token = localStorage.getItem('token')
          if (token) {
            headers['Authorization'] = `Token ${token}`
          }

          let res = await fetch(`/api/files/${fileId}/download/`, { headers, signal: controller.signal })
          // 如果服务端未接受Range或返回全量，则重新开始
          if (shouldResume && existingSize > 0 && res.status === 200) {
            existingSize = 0
            res = await fetch(`/api/files/${fileId}/download/`, { signal: controller.signal })
          }

          // 拒绝返回网页/JSON错误响应，避免把错误页面保存成 4KB HTML
          const ct = res.headers.get('content-type') || ''
          if (!res.ok || /text\/html/i.test(ct) || /application\/json/i.test(ct)) {
            let errText
            try {
              errText = await res.text()
            } catch (_) {}
            
            // 检查是否是可重试的错误
            const isRetryableError = res.status >= 500 || res.status === 408 || res.status === 429
            const errorMessage = errText || `下载失败，HTTP ${res.status}`
            
            if (isRetryableError) {
              throw new Error(`RETRYABLE: ${errorMessage}`)
            } else {
              throw new Error(errorMessage)
            }
          }

          const totalFromRange = (() => {
            const cr = res.headers.get('content-range')
            if (!cr) return null
            const parts = cr.split('/')
            const totalStr = parts[1]
            return parseInt(totalStr, 10)
          })()
          const totalSize = Number.isFinite(totalFromRange) ? totalFromRange : (fileSize || 0)
          const contentLength = parseInt(res.headers.get('content-length') || '0', 10)

          // 如果返回体长度为 0，则直接报错，避免生成空文件
          if (!Number.isFinite(contentLength) || contentLength === 0) {
            throw new Error('下载失败，服务端返回空内容')
          }

          writable = await fileHandle.createWritable()
          const reader = res.body.getReader()
          let received = 0
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            // 如果外部已请求暂停/取消，立即中断并停止更新进度
            if (this.downloadPauseRequested[fileId] || this.downloadCancelRequested[fileId]) {
              try { controller.abort() } catch (_) {}
              break
            }
            received += value.length
            // 断点写入到指定位置
            await writable.write({ type: 'write', position: existingSize + received - value.length, data: value })

            const denominator = totalSize || (existingSize + contentLength || existingSize + received)
            const percent = denominator ? Math.round(((existingSize + received) * 100) / denominator) : 0
            this.downloadProgress[fileId] = Math.min(percent, 100)
          }
          await writable.close()
          writable = null
        } else {
          // 不支持文件系统访问 API 的回退：开始请求即视为下载中
          this.downloadActive[fileId] = true
          if ((fileSize || 0) >= ONE_GB) {
            this.error = '当前浏览器不支持断点续传，请使用最新的 Chromium 内核浏览器（如 Chrome）。'
            return { success: false, error: this.error }
          }
          // Fallback: 使用XHR（axios）下载Blob，同时尝试显示下载进度
          const token = localStorage.getItem('token')
          const response = await axios.get(`/api/files/${fileId}/download/`, {
            responseType: 'blob',
            headers: token ? { Authorization: `Token ${token}` } : undefined,
            signal: controller.signal,
            onDownloadProgress: (progressEvent) => {
              // 暂停/取消时不再更新百分比
              if (this.downloadPauseRequested[fileId] || this.downloadCancelRequested[fileId]) return
              const loaded = progressEvent.loaded || 0
              const total = progressEvent.total || fileSize || 0
              if (total) {
                this.downloadProgress[fileId] = Math.round((loaded * 100) / total)
              }
            }
          })
          // 若返回体大小为 0，则判定为失败，避免保存空文件
          if (response?.data && typeof response.data.size === 'number' && response.data.size === 0) {
            throw new Error('下载失败，返回空文件')
          }
          // 检查返回的 Blob 类型，避免保存 HTML/JSON
          const blobType = response.data?.type || ''
          if (/text\/html/i.test(blobType) || /application\/json/i.test(blobType)) {
            // 尝试读取错误信息
            try {
              const reader = new FileReader()
              const text = await new Promise((resolve) => {
                reader.onload = () => resolve(reader.result)
                reader.readAsText(response.data)
              })
              throw new Error(typeof text === 'string' && text.length ? text : '下载失败，返回错误页面')
            } catch (e) {
              throw new Error('下载失败，返回错误页面')
            }
          }
          const url = window.URL.createObjectURL(new Blob([response.data]))
          const link = document.createElement('a')
          link.href = url
          link.setAttribute('download', filename)
          document.body.appendChild(link)
          link.click()
          link.remove()
          window.URL.revokeObjectURL(url)
        }
        cleanup('success')
        delete this.downloadHandles[fileId]
        if (window.__downloadHandles) delete window.__downloadHandles[fileId]
        return { success: true, message: '文件下载成功' }
      } catch (error) {
        // 捕获暂停标记
        const pausedFlag = !!this.downloadPauseRequested[fileId]
        const aborted = error && (error.name === 'AbortError' || error.code === 'ERR_CANCELED' || /aborted/i.test(error.message || ''))
        // 取消场景下丢弃未提交内容，暂停则保留以便续传
        if (aborted && !pausedFlag) {
          try {
            if (typeof window.showSaveFilePicker === 'function' && typeof WritableStream !== 'undefined') {
              if (writable && typeof writable.abort === 'function') {
                await writable.abort()
              }
            }
          } catch (_) {}
          // 尽力清理任何已创建的残留文件内容
          try {
            if (fileHandle && typeof fileHandle.createWritable === 'function') {
              const w2 = await fileHandle.createWritable()
              if (typeof w2.truncate === 'function') {
                await w2.truncate(0)
              }
              await w2.close()
              // 若支持目录选择，尝试删除该文件（需用户选择所在目录）
              try {
                if (typeof window.showDirectoryPicker === 'function' && fileHandle.name) {
                  const dir = await window.showDirectoryPicker()
                  try {
                    const qp = await dir.queryPermission?.({ mode: 'readwrite' })
                    if (qp !== 'granted') {
                      await dir.requestPermission?.({ mode: 'readwrite' })
                    }
                  } catch (_) {}
                  try {
                    await dir.getFileHandle(fileHandle.name, { create: false })
                    await dir.removeEntry(fileHandle.name)
                  } catch (_) {}
                }
              } catch (_) {}
            }
          } catch (_) {}
        }
        // 暂停时主动 close 以提交已写入的内容，方便后续读取 existingSize 断点续传
        if (aborted && pausedFlag) {
          try {
            if (writable && typeof writable.close === 'function') {
              await writable.close()
            }
          } catch (_) {}
        }

        let message
        if (aborted) {
          message = pausedFlag ? '' : '下载已取消'
        } else {
          // 提供更清晰的错误信息
          if (error?.response?.status === 404) {
            message = '文件不存在或已被删除'
          } else if (error?.response?.status === 403) {
            message = '没有权限下载此文件'
          } else if (error?.response?.status === 401) {
            message = '登录已过期，请重新登录'
          } else if (error?.response?.status >= 500) {
            message = '服务器错误，请稍后重试'
          } else if (error?.name === 'TypeError' || error?.message?.includes('fetch')) {
            message = '网络连接失败，请检查网络连接'
          } else if (error?.message?.includes('timeout')) {
            message = '下载超时，请重试'
          } else if (error?.message?.includes('空文件')) {
            message = '文件为空或损坏'
          } else if (error?.message?.includes('错误页面')) {
            message = '服务器返回错误，请联系管理员'
          } else {
            message = error?.message 
              || error?.response?.data?.message 
              || error?.response?.data?.error 
              || error?.response?.data?.detail 
              || '文件下载失败，请重试'
          }
          console.error(`Download error (attempt ${retryCount + 1}/${maxRetries + 1}):`, error)
        }

        // 检查是否可以重试
        const isRetryableError = !aborted && (
          error?.message?.includes('RETRYABLE:') ||
          error?.name === 'TypeError' ||
          error?.message?.includes('fetch') ||
          error?.message?.includes('network') ||
          error?.message?.includes('timeout') ||
          (error?.response && error.response.status >= 500)
        )

        if (isRetryableError && retryCount < maxRetries) {
          console.log(`Retrying download in ${retryDelay * (retryCount + 1)}ms...`)
          
          // 清理当前状态但保留进度
          delete this.downloadControllers[fileId]
          delete this.downloadPauseRequested[fileId]
          delete this.downloadCancelRequested[fileId]
          
          // 延迟重试
          setTimeout(() => {
            this.downloadFile(fileId, filename, fileSize, {
              ...opts,
              retryCount: retryCount + 1,
              maxRetries,
              retryDelay,
              useExistingHandle: true // 重试时使用现有句柄
            })
          }, retryDelay * (retryCount + 1))
          
          return { success: false, error: `正在重试下载... (${retryCount + 1}/${maxRetries})` }
        }

        // 按模式清理
        const mode = aborted ? (pausedFlag ? 'pause' : 'cancel') : 'error'
        cleanup(mode)
        if (mode !== 'pause') {
          const cleanMessage = message.replace('RETRYABLE: ', '')
          this.error = cleanMessage
          delete this.downloadHandles[fileId]
          if (window.__downloadHandles) delete window.__downloadHandles[fileId]
          
          // 显示错误通知（仅在非重试情况下显示）
          if (mode === 'error' && retryCount === 0) {
            this.showErrorNotification(`下载失败: ${cleanMessage}`)
          } else if (mode === 'cancel') {
            this.showErrorNotification('下载已取消')
          }
        }
        return { success: false, error: message.replace('RETRYABLE: ', '') }
      }
    },

    pauseDownload(fileId) {
      if (this.downloadControllers[fileId]) {
        this.downloadPauseRequested[fileId] = true
        this.downloadPaused[fileId] = true
        try { this.downloadControllers[fileId].abort() } catch (_) {}
      }
    },

    async cancelDownload(fileId) {
      // 标记取消
      this.downloadCancelRequested[fileId] = true
      // 防止“暂停后立刻取消”被误判为暂停，直接清除暂停标记
      this.downloadPauseRequested[fileId] = false
      this.downloadPaused[fileId] = false
      // 乐观更新 UI：让进度和按钮立即复位
      delete this.downloadProgress[fileId]
      delete this.downloadActive[fileId]
      const controller = this.downloadControllers[fileId]
      if (controller) {
        // 正在下载：通过 abort() 走统一的错误捕获与清理
        try { controller.abort() } catch (_) {}
      } else {
        // 已暂停且控制器已清理：手动清理并尽力删除/清空本地残留
        try {
          const handle = (this.downloadHandles[fileId] || (window.__downloadHandles && window.__downloadHandles[fileId]))
          if (handle && handle.createWritable) {
            try { await handle.requestPermission?.({ mode: 'readwrite' }) } catch (_) {}
            const w = await handle.createWritable()
            // 截断为 0，以避免残留内容
            if (typeof w.truncate === 'function') {
              await w.truncate(0)
            }
            await w.close()
            // 若支持目录选择，尝试删除该文件（需要用户选择所在目录）
            try {
              if (typeof window.showDirectoryPicker === 'function' && handle.name) {
                const dir = await window.showDirectoryPicker()
                try {
                  const qp = await dir.queryPermission?.({ mode: 'readwrite' })
                  if (qp !== 'granted') {
                    await dir.requestPermission?.({ mode: 'readwrite' })
                  }
                } catch (_) {}
                try {
                  // 仅当该目录存在该文件时才删除
                  await dir.getFileHandle(handle.name, { create: false })
                  await dir.removeEntry(handle.name)
                } catch (_) {}
              }
            } catch (_) {}
          }
        } catch (_) {}
        // 手动清理状态
        delete this.downloadProgress[fileId]
        delete this.downloadActive[fileId]
        delete this.downloadPaused[fileId]
        delete this.downloadControllers[fileId]
        delete this.downloadPauseRequested[fileId]
        delete this.downloadCancelRequested[fileId]
        if (this.downloadHandles[fileId]) delete this.downloadHandles[fileId]
        if (window.__downloadHandles) delete window.__downloadHandles[fileId]
      }
    },

    async resumeDownload(fileId, filename, fileSize) {
      this.downloadPaused[fileId] = false
      return await this.downloadFile(fileId, filename, fileSize, { useExistingHandle: true })
    },

    // 新增：界面控制方法
    setViewMode(mode) {
      this.viewMode = mode
    },

    toggleUploadDialog() {
      this.showUploadDialog = !this.showUploadDialog
    },

    toggleNewFolderDialog() {
      this.showNewFolderDialog = !this.showNewFolderDialog
    },

    closeAllDialogs() {
      this.showUploadDialog = false
      this.showNewFolderDialog = false
    },

    showDownloadNotification(message) {
      this.showNotification(message, 'success')
    },

    showErrorNotification(message) {
      this.showNotification(message, 'error')
    },

    showNotification(message, type = 'success') {
      // 创建通知
      const notification = document.createElement('div')
      const isError = type === 'error'
      const backgroundColor = isError ? '#f44336' : '#4CAF50'
      const icon = isError ? '⚠️' : '✓'
      
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${backgroundColor};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        font-size: 14px;
        max-width: 350px;
        word-wrap: break-word;
        animation: slideIn 0.3s ease-out;
        display: flex;
        align-items: center;
        gap: 8px;
      `
      
      // 添加滑入动画
      const style = document.createElement('style')
      style.textContent = `
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `
      if (!document.head.querySelector('style[data-notification]')) {
        style.setAttribute('data-notification', 'true')
        document.head.appendChild(style)
      }
      
      notification.innerHTML = `<span style="font-size: 16px;">${icon}</span><span>${message}</span>`
      document.body.appendChild(notification)
      
      // 错误信息显示更长时间（5秒），成功信息3秒
      const duration = isError ? 5000 : 3000
      setTimeout(() => {
        if (notification.parentNode) {
          notification.style.animation = 'slideIn 0.3s ease-out reverse'
          setTimeout(() => {
            if (notification.parentNode) {
              notification.parentNode.removeChild(notification)
            }
          }, 300)
        }
      }, duration)
    },

    showLoadingOverlay(message = 'Cellxgene 正在加载数据，请稍候...') {
      this.loadingOverlayVisible = true
      this.loadingOverlayMessage = message
    },

    hideLoadingOverlay() {
      this.loadingOverlayVisible = false
      this.loadingOverlayMessage = '请稍候...'
    },

    setLastCellxgeneFile(filename) {
      this.lastPublishedCellxgeneFile = filename
    },

    // 搜索相关方法
    async searchFiles(params) {
      try {
        const response = await axios.get('/api/files/search/', { params })
        return response.data
      } catch (error) {
        console.error('搜索文件失败:', error)
        throw error
      }
    },

    async getFacets() {
      try {
        const response = await axios.get('/api/files/facets/')
        return response.data
      } catch (error) {
        console.error('获取筛选器数据失败:', error)
        throw error
      }
    },

    async getSearchSuggestions(query, limit = 10) {
      try {
        const response = await axios.get('/api/files/suggestions/', {
          params: { q: query, limit }
        })
        return response.data
      } catch (error) {
        console.error('获取搜索建议失败:', error)
        throw error
      }
    },

    async getFilePreview(fileId) {
      try {
        const response = await axios.get(`/api/files/${fileId}/preview/`)
        return response.data
      } catch (error) {
        console.error('获取文件预览失败:', error)
        throw error
      }
    },

    async uploadFileWithMetadata(file, metadata, parentFolderId = null) {
      this.isLoading = true
      this.error = null
      this.uploadProgress = 0
      this.uploadPauseRequested = false
      this.uploadCancelRequested = false
      this.uploadPaused = false
      this.uploadSessionId = null
      this.uploadUploadedSize = 0
      this.uploadFileRef = file
      this.uploadMethodRef = 'Enhanced Vue Frontend'

      try {
        // 创建FormData
        const formData = new FormData()
        formData.append('file', file)
        formData.append('upload_method', this.uploadMethodRef)
        
        // 添加元数据字段
        formData.append('title', metadata.title || '')
        formData.append('project', metadata.project || '')
        formData.append('file_format', metadata.file_format || 'other')
        formData.append('document_type', metadata.document_type || 'Dataset')
        formData.append('access_level', metadata.access_level || 'Internal')
        formData.append('organism', metadata.organism || '')
        formData.append('experiment_type', metadata.experiment_type || '')
        formData.append('tags', metadata.tags || '')
        formData.append('description', metadata.description || '')
        
        if (parentFolderId) {
          formData.append('parent_folder', parentFolderId)
        }

        // 使用XMLHttpRequest以支持进度监控
        return new Promise((resolve, reject) => {
          const xhr = new XMLHttpRequest()
          
          // 进度监控
          xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
              this.uploadProgress = Math.round((event.loaded / event.total) * 100)
            }
          })
          
          // 完成处理
          xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              try {
                const response = JSON.parse(xhr.responseText)
                resolve(response)
              } catch (e) {
                reject(new Error('响应解析失败'))
              }
            } else {
              try {
                const errorResponse = JSON.parse(xhr.responseText)
                reject(new Error(errorResponse.message || '上传失败'))
              } catch (e) {
                reject(new Error(`上传失败: ${xhr.status}`))
              }
            }
          })
          
          // 错误处理
          xhr.addEventListener('error', () => {
            reject(new Error('网络错误'))
          })
          
          // 中止处理
          xhr.addEventListener('abort', () => {
            reject(new Error('上传被取消'))
          })
          
          // 发送请求
          xhr.open('POST', '/api/files/upload/')
          
          // 添加认证头
          const token = localStorage.getItem('token')
          if (token) {
            xhr.setRequestHeader('Authorization', `Token ${token}`)
          }
          
          xhr.send(formData)
          
          // 保存控制器以便取消
          this.uploadController = xhr
        })
        
      } catch (error) {
        this.error = error.message || '上传失败'
        throw error
      } finally {
        this.isLoading = false
        this.uploadProgress = 0
        this.uploadController = null
      }
    }
  }
})