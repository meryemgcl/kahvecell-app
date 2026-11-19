import { useToastStore } from '../store/toastStore'

export default function ToastStack() {
  const toasts = useToastStore((state) => state.toasts)
  const dismiss = useToastStore((state) => state.dismiss)

  return (
    <aside className="toast-stack" aria-live="polite" aria-label="Bildirimler">
      {toasts.map((toast) => (
        <div className={`toast toast-${toast.type}`} key={toast.id} role={toast.type === 'error' ? 'alert' : 'status'}>
          <span className="toast-icon" aria-hidden="true">
            {toast.type === 'success' ? '✓' : '!'}
          </span>
          <p>{toast.message}</p>
          <button type="button" aria-label="Bildirimi kapat" onClick={() => dismiss(toast.id)}>
            ×
          </button>
        </div>
      ))}
    </aside>
  )
}
