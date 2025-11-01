<template>
  <nav class="navbar navbar-default waves-transparent" role="navigation">
    <div class="container-fluid">
      <div class="navbar-header">
        <router-link to="/" class="navbar-brand">
          <img :src="logoUrl" alt="WAVES Logo" id="navbar-logo" />
          <span class="brand-text">Download System</span>
        </router-link>
      </div>
      
      <div class="navbar-collapse collapse in">
        <ul class="nav navbar-nav navbar-right">
          <!-- 主要导航项 -->
          <li :class="{ active: $route.path === '/' }">
            <router-link to="/">Home</router-link>
          </li>
          
          <template v-if="isAuthenticated">
            <li :class="{ active: $route.path === '/files' }">
              <router-link to="/files">📁 文件管理</router-link>
            </li>
            <li :class="{ active: $route.path === '/search' }">
              <router-link to="/search">🔍 文件查找</router-link>
            </li>
            <li :class="{ active: $route.path === '/upload' }">
              <router-link to="/upload">📤 文件上传</router-link>
            </li>
            <li :class="{ active: $route.path === '/profile' }">
              <router-link to="/profile">👤 个人资料</router-link>
            </li>
          </template>

          
          <!-- 用户相关项 -->
          <template v-if="!isAuthenticated">
            <li :class="{ active: $route.path === '/login' }">
              <router-link to="/login">Login</router-link>
            </li>
          </template>
          
          <template v-if="isAuthenticated">
            <li>
              <a href="#" @click.prevent="handleLogout">Logout</a>
            </li>
          </template>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import logoUrl from '../assets/images/logo.png'

export default {
  name: 'Navbar',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    const currentUser = computed(() => authStore.currentUser)
    
    const handleLogout = async () => {
      await authStore.logout()
      router.push('/')
    }
    
    return {
      isAuthenticated,
      currentUser,
      handleLogout,
      logoUrl
    }
  }
}
</script>

<style scoped>
.navbar.waves-transparent {
  background: var(--waves-navbar-transparent-bg);
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  min-height: 50px;
  padding: 8px 0;
}

.navbar .container-fluid {
  padding-left: 10px;
}

.navbar-brand {
  display: flex;
  align-items: center;
  color: var(--waves-corporate-text) !important;
  font-weight: 600;
  text-decoration: none;
}

.navbar-brand:hover {
  color: var(--waves-corporate-text-light) !important;
  text-decoration: none;
}

#navbar-logo {
  height: 32px;
  width: auto;
  margin-right: 5px;
  margin-top: -2px;
}

.navbar-brand .brand-text {
  font-size: 18px;
  font-weight: 600;
  color: #4a4a4a !important;
  text-shadow: none !important;
  margin-top: -px;
}

.navbar-nav > li > a {
  display: inline-block;
  margin-top: 12px; /* 现在会明显下移 */
  padding: 6px 13px !important;
  font-size: 14px;
}


.navbar-nav > li > a:hover,
.navbar-nav > li > a:focus {
  color: var(--waves-corporate-text-light) !important;
  background-color: rgba(0, 0, 0, 0.05) !important;
  text-decoration: none;
}

.navbar-nav > li.active > a,
.navbar-nav > li.active > a:hover,
.navbar-nav > li.active > a:focus {
  color: var(--brand-accent) !important;
  background-color: rgba(37, 99, 235, 0.1) !important;
  border-radius: var(--waves-radius-sm);
}

.navbar-text {
  color: var(--waves-corporate-text-light) !important;
  font-weight: 500;
  margin: 15px 15px !important;
}



@media (max-width: 767px) {
  .navbar-collapse {
    background: var(--waves-navbar-transparent-bg);
    border-top: 1px solid rgba(0, 0, 0, 0.1);
    margin-top: 10px;
    padding-top: 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }
  
  .brand-text {
    font-size: 16px;
  }
  
  #navbar-logo {
    height: 28px;
  }
  
  .navbar-nav > li > a {
    padding: 12px 15px !important;
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  }
  
  .navbar-nav > li:last-child > a {
    border-bottom: none;
  }
  
  .navbar-text {
    padding: 12px 15px !important;
    margin: 0 !important;
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  }
}

@media (min-width: 768px) and (max-width: 991px) {
  .brand-text {
    font-size: 17px;
  }
  
  #navbar-logo {
    height: 30px;
  }
  
  .navbar-nav > li > a {
    padding: 15px 12px;
  }
}
</style>