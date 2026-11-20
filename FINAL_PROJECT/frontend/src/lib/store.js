import { create } from 'zustand'

const API_BASE = '/api'

// Auth store
export const useAuthStore = create((set, get) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),

  login: async (username, password) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Login failed')
    localStorage.setItem('token', data.token)
    set({ user: data.user, token: data.token, isAuthenticated: true })
    return data
  },

  register: async (userData) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.error || 'Registration failed')
    localStorage.setItem('token', data.token)
    set({ user: data.user, token: data.token, isAuthenticated: true })
    return data
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null, isAuthenticated: false })
  },

  fetchMe: async () => {
    const token = get().token
    if (!token) return
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.ok) {
        const data = await res.json()
        set({ user: data, isAuthenticated: true })
      } else {
        get().logout()
      }
    } catch {
      // silently fail
    }
  },
}))

// Verification store
export const useVerificationStore = create((set) => ({
  result: null,
  layerProgress: {},
  isVerifying: false,
  error: null,

  setResult: (result) => set({ result, isVerifying: false }),
  setLayerProgress: (layer, data) =>
    set((state) => ({
      layerProgress: { ...state.layerProgress, [layer]: data },
    })),
  startVerification: () =>
    set({ isVerifying: true, error: null, layerProgress: {}, result: null }),
  setError: (error) => set({ error, isVerifying: false }),
  reset: () =>
    set({ result: null, layerProgress: {}, isVerifying: false, error: null }),
}))

// API helper
export const apiFetch = async (url, options = {}) => {
  const token = localStorage.getItem('token')
  const headers = { ...options.headers }
  if (token) headers.Authorization = `Bearer ${token}`
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(`${API_BASE}${url}`, { ...options, headers })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || `Request failed (${res.status})`)
  }
  return res.json()
}
