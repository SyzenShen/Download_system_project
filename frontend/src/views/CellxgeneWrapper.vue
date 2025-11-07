<template>
  <div class="cellxgene-wrapper">
    <section v-if="loadError" class="helper-panel">
      <div class="helper-card">
        <div class="helper-title">未检测到可用的 Cellxgene 页面</div>
        <div class="helper-body">
          <p>请确认已在本机启动 Cellxgene 并加载数据集：</p>
          <pre class="helper-code">cellxgene launch /path/to/your.h5ad --port 5005</pre>
          <p>或在环境变量中配置地址：</p>
          <pre class="helper-code">VITE_CELLXGENE_URL=http://your-host:your-port/</pre>
          <div class="helper-actions">
            <a :href="externalUrl" target="_blank" rel="noopener" class="open-external">在新标签打开</a>
            <button class="retry-btn" @click="retryCheck">重试检测</button>
          </div>
        </div>
      </div>
    </section>

    <section v-else class="wrapper-content">
      <iframe
        class="wrapper-iframe"
        :src="iframeSrc"
        frameborder="0"
        allowfullscreen
      ></iframe>
    </section>
  </div>
  
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'CellxgeneWrapper',
  setup() {
    const route = useRoute()
    const fileName = route.query.file
    
    // 构建iframe源URL，如果有文件名参数则添加到URL中
    const baseUrl = import.meta.env.VITE_CELLXGENE_URL || '/cellxgene/'
    const iframeSrc = computed(() => {
      if (!fileName) return baseUrl
      // 移除尾部斜杠并添加文件参数（兼容 Cellxgene 标准 dataset 参数）
      const cleanBaseUrl = baseUrl.replace(/\/$/, '')
      return `${cleanBaseUrl}?dataset=${encodeURIComponent(fileName)}`
    })
    
    const externalUrl = computed(() => {
      const baseExtUrl = (import.meta.env.VITE_CELLXGENE_URL || 'http://localhost:5005/').replace(/\/$/, '')
      if (!fileName) return baseExtUrl
      return `${baseExtUrl}?dataset=${encodeURIComponent(fileName)}`
    })
    
    const loadError = ref(false)
    let retryTimer = null

    const checkAvailability = async () => {
      try {
        const isExternal = /^https?:\/\//.test(baseUrl)
        if (isExternal) {
          loadError.value = false
          return
        }
        const cleanBaseUrl = baseUrl.replace(/\/$/, '')
        const healthUrl = `${cleanBaseUrl}/api/v0.2/config`
        const res = await fetch(healthUrl, { method: 'GET' })
        loadError.value = !res.ok
      } catch (e) {
        console.warn('Cellxgene 可用性检测失败:', e)
        loadError.value = true
      }
      if (loadError.value) {
        retryTimer = setTimeout(checkAvailability, 3000)
      }
    }

    const retryCheck = () => checkAvailability()

    const goBack = () => {
      window.location.href = '/files'
    }

    onMounted(() => {
      checkAvailability()
    })

    onUnmounted(() => {
      if (retryTimer) {
        clearTimeout(retryTimer)
      }
    })

    return { iframeSrc, externalUrl, loadError, goBack, retryCheck, fileName }
  }
}
</script>

<style scoped>
.cellxgene-wrapper {
  position: fixed;
  top: 72px; /* 保留导航栏 */
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  background: var(--waves-surface-primary);
  padding: 16px;
  box-sizing: border-box;
  overflow: hidden;
}

.wrapper-content {
  flex: 1;
  display: flex;
  min-height: 0;
}

.wrapper-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: #fff;
}

.helper-panel {
  padding: 16px;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.helper-card {
  border: 1px solid var(--waves-border-light);
  border-radius: var(--waves-radius-sm);
  background: var(--bg-card);
  padding: 16px;
}

.helper-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.helper-code {
  background: #f7f7f7;
  padding: 8px;
  border-radius: var(--waves-radius-sm);
  border: 1px solid var(--waves-border-light);
}

.helper-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.open-external, .retry-btn {
  padding: 8px 12px;
  border: 1px solid var(--waves-border-light);
  border-radius: var(--waves-radius-sm);
  background: #fff;
  color: var(--waves-text-primary);
  cursor: pointer;
  text-decoration: none;
}
</style>