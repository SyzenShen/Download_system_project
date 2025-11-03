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
import { ref, onMounted } from 'vue'

export default {
  name: 'CellxgeneWrapper',
  setup() {
    const iframeSrc = import.meta.env.VITE_CELLXGENE_URL || '/cellxgene/'
    const externalUrl = (import.meta.env.VITE_CELLXGENE_URL || 'http://localhost:5005/').replace(/\/$/, '/')
    const loadError = ref(false)

    const checkAvailability = async () => {
      try {
        const res = await fetch(iframeSrc, { method: 'GET' })
        // 期望 200 或 302，其他状态视为不可用
        loadError.value = !(res.status >= 200 && res.status < 400)
      } catch (e) {
        loadError.value = true
      }
    }

    const retryCheck = () => checkAvailability()

    const goBack = () => {
      window.location.href = '/files'
    }

    onMounted(() => {
      checkAvailability()
    })

    return { iframeSrc, externalUrl, loadError, goBack, retryCheck }
  }
}
</script>

<style scoped>
.cellxgene-wrapper {
  position: fixed;
  top: 72px; /* 保留顶部导航栏，以下区域全屏（与 Navbar 高度一致） */
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  background: var(--waves-surface-primary);
}

.wrapper-content {
  flex: 1;
  display: flex;
}

.wrapper-iframe {
  width: 100%;
  height: 100%;
  background: #fff;
}

.helper-panel {
  padding: 16px;
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