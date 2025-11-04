<template>
  <teleport to="body">
    <div v-if="isVisible" class="cxg-overlay">
      <div class="cxg-overlay__card">
        <div class="cxg-overlay__spinner"></div>
        <div class="cxg-overlay__text">{{ overlayMessage }}</div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useFilesStore } from '../stores/files'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  message: {
    type: String,
    default: '请稍候...'
  }
})

const filesStore = useFilesStore()
const isVisible = computed(() => filesStore.loadingOverlayVisible)
const overlayMessage = computed(() => filesStore.loadingOverlayMessage || props.message)
</script>

<style scoped>
.cxg-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20000;
}

.cxg-overlay__card {
  background: rgba(20, 20, 20, 0.85);
  border-radius: 12px;
  padding: 28px 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
  min-width: 220px;
}

.cxg-overlay__spinner {
  border: 4px solid rgba(255, 255, 255, 0.25);
  border-top-color: #4CAF50;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  animation: cxg-spin 0.8s linear infinite;
}

.cxg-overlay__text {
  color: #fff;
  font-size: 15px;
  text-align: center;
}

@keyframes cxg-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
