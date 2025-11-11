import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    isLoading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user
  },

  actions: {
    async login(credentials) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await axios.post('/api/auth/login/', credentials)
        const { token, user } = response.data
        
        this.token = token
        this.user = user
        localStorage.setItem('token', token)
        
        // Configure default axios headers
        axios.defaults.headers.common['Authorization'] = `Token ${token}`
        
        return { success: true }
      } catch (error) {
        // Prefer backend validation errors when available
        const data = error.response?.data
        const msgFromSerializer = Array.isArray(data?.non_field_errors) ? data.non_field_errors[0]
          : (typeof data === 'string' ? data : null)
        const fallback = data?.message || data?.detail
        this.error = msgFromSerializer || fallback || 'Incorrect email or password'
        return { success: false, error: this.error }
      } finally {
        this.isLoading = false
      }
    },

    async register(userData) {
      this.isLoading = true
      this.error = null
      
      try {
        const response = await axios.post('/api/auth/register/', userData)
        return { success: true, message: 'Registration successful, please sign in.' }
      } catch (error) {
        const data = error.response?.data
        // Serializer errors can be lists or dicts; flatten them
        let specificError = null
        if (typeof data === 'object' && data) {
          const fieldOrder = ['username', 'email', 'password', 'confirm_password', 'non_field_errors']
          for (const field of fieldOrder) {
            if (Array.isArray(data[field]) && data[field].length) {
              specificError = data[field][0]
              break
            }
          }
        }
        const fallback = data?.message || data?.detail
        this.error = specificError || fallback || 'Registration failed'
        return { success: false, error: this.error }
      } finally {
        this.isLoading = false
      }
    },

    async logout() {
      try {
        await axios.post('/api/auth/logout/')
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        this.token = null
        this.user = null
        localStorage.removeItem('token')
        delete axios.defaults.headers.common['Authorization']
      }
    },

    async fetchUser() {
      if (!this.token) return
      
      try {
        const response = await axios.get('/api/auth/profile/')
        this.user = response.data
      } catch (error) {
        console.error('Fetch user error:', error)
        // Do not force logout; keep the token so the user can retry or refresh
        delete axios.defaults.headers.common['Authorization']
      }
    },

    initializeAuth() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Token ${this.token}`
        this.fetchUser()
      }
    }
  }
})
