<template>
  <div id="app" class="app-full-center">
    <Navbar />
    <main class="container">
      <transition name="fade" mode="out-in">
        <router-view />
      </transition>
    </main>
  </div>
</template>

<script>
import Navbar from './components/Navbar.vue'

export default {
  name: 'App',
  components: {
    Navbar
  }
}
</script>
<style>
/* 全局路由渐隐/渐显过渡 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 250ms ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>