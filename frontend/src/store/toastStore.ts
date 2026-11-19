import { create } from 'zustand'

export type Toast = {
  id: number
  type: 'success' | 'error'
  message: string
}

type ToastState = {
  toasts: Toast[]
  show: (message: string, type?: 'success' | 'error') => void
  dismiss: (id: number) => void
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  show: (message, type = 'success') => {
    const id = Date.now() + Math.floor(Math.random() * 1000)
    set((state) => ({ toasts: [...state.toasts, { id, type, message }] }))
    window.setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }))
    }, 4200)
  },
  dismiss: (id) => {
    set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) }))
  },
}))
