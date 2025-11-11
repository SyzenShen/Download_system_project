import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

// Import view components
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import FileList from '../views/FileList.vue'
import FileUpload from '../views/FileUpload.vue'
import FileSearch from '../views/FileSearch.vue'
import UploadTest from '../views/UploadTest.vue'
import CellxgeneWrapper from '../views/CellxgeneWrapper.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresGuest: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/files',
    name: 'FileList',
    component: FileList,
    meta: { requiresAuth: true }
  },
  {
    path: '/upload',
    name: 'FileUpload',
    component: FileUpload,
    meta: { requiresAuth: true }
  },
  {
    path: '/search',
    name: 'FileSearch',
    component: FileSearch,
    meta: { requiresAuth: true }
  },
  {
    path: '/upload-test',
    name: 'UploadTest',
    component: UploadTest,
    meta: { requiresAuth: true }
  },
  {
    path: '/cellxgene-app',
    name: 'CellxgeneWrapper',
    component: CellxgeneWrapper,
    // Allow all users to open the Cellxgene wrapper to avoid blocking viewers without a session
    meta: {}
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Router guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
