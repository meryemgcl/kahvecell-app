import { create } from 'zustand'

type AuthState = {
  accessToken: string | null
  refreshToken: string | null
  role: 'CUSTOMER' | 'SHOP_OWNER' | 'ADMIN' | null
  setTokens: (accessToken: string, refreshToken: string) => void
  setRole: (role: 'CUSTOMER' | 'SHOP_OWNER' | 'ADMIN') => void
  clearTokens: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: localStorage.getItem('kahvecell_access_token'),
  refreshToken: localStorage.getItem('kahvecell_refresh_token'),
  role: localStorage.getItem('kahvecell_role') as AuthState['role'],
  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem('kahvecell_access_token', accessToken)
    localStorage.setItem('kahvecell_refresh_token', refreshToken)
    set({ accessToken, refreshToken })
  },
  setRole: (role) => {
    localStorage.setItem('kahvecell_role', role)
    set({ role })
  },
  clearTokens: () => {
    localStorage.removeItem('kahvecell_access_token')
    localStorage.removeItem('kahvecell_refresh_token')
    localStorage.removeItem('kahvecell_role')
    set({ accessToken: null, refreshToken: null, role: null })
  },
}))
