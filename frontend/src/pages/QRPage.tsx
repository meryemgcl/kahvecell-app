import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import client from '../api/client'
import PageState from '../components/PageState'
import { useToastStore } from '../store/toastStore'

type Order = {
  id: string
  status: string
  shop_name?: string | null
  product_name?: string | null
  qr_payload: {
    order_id: string
    user_id: string
    shop_id: string
    created_at: string
    signature: string
  }
  qr_code_data_url: string
}

export default function QRPage() {
  const { orderId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const routeOrder = (location.state as { order?: Order } | null)?.order
  const [order, setOrder] = useState<Order | null>(routeOrder || null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(!routeOrder)
  const [retryVersion, setRetryVersion] = useState(0)
  const showToast = useToastStore((state) => state.show)

  useEffect(() => {
    if (!orderId) return

    let active = true
    let eventSource: EventSource | null = null

    async function loadOrder() {
      try {
        const response = await client.get<Order>(`/orders/${orderId}`)
        if (active) {
          setOrder(response.data)
          setError('')
          setLoading(false)
        }
      } catch {
        if (active) {
          setError('Sipariş durumu güncellenemedi.')
          setLoading(false)
        }
      }
    }

    if (!routeOrder) {
      loadOrder()
    } else {
      setLoading(false)
    }

    const accessToken = localStorage.getItem('kahvecell_access_token')
    if (accessToken) {
      const apiBase =
        import.meta.env.VITE_API_BASE_URL ||
        'http://127.0.0.1:8000/api/v1'
      eventSource = new EventSource(
        `${apiBase}/orders/${orderId}/stream?access_token=${encodeURIComponent(accessToken)}`,
      )

      eventSource.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data) as {
            order_id: string
            status: string
          }
          setOrder((current) =>
            current
              ? { ...current, status: update.status }
              : current,
          )
          setLoading(false)
          setError('')
          if (update.status === 'DELIVERED') {
            showToast('Sipariş teslim edildi. Afiyet olsun!', 'success')
            eventSource?.close()
          }
        } catch {
          setError('Sipariş bildirimi okunamadı.')
          setLoading(false)
        }
      }

      eventSource.onerror = () => {
        if (active && eventSource?.readyState === EventSource.CLOSED) {
          setError('Canlı bildirim bağlantısı kesildi.')
          setLoading(false)
        }
      }
    }

    return () => {
      active = false
      eventSource?.close()
    }
  }, [orderId, retryVersion])

  const statusLabels: Record<string, string> = {
    PENDING: 'Bekliyor',
    ACCEPTED: 'Kabul Edildi',
    PREPARING: 'Hazırlanıyor',
    READY: 'Hazır',
    DELIVERED: 'Teslim Edildi',
  }

  const statusLabel = order ? statusLabels[order.status] || order.status : ''
  const delivered = order?.status === 'DELIVERED'

  return (
    <main className="qr-page">
      <button className="back-button" type="button" onClick={() => navigate('/')}>
        ← Ana sayfa
      </button>
      <section className="qr-card">
        <p className="order-eyebrow">Sipariş onaylandı</p>
        <h1>{delivered ? 'Afiyet olsun!' : 'QR Kodun Hazır'}</h1>
        {loading && <PageState type="loading" message="Sipariş bilgileri yükleniyor..." />}
        {!loading && error && (
          <PageState type="error" message={error} onRetry={() => setRetryVersion((value) => value + 1)} />
        )}
        {!loading && !error && !order && (
          <PageState
            type="empty"
            title="Sipariş bulunamadı"
            message="Geçmişe dönüp siparişini tekrar açabilirsin."
            actionLabel="Geçmişe Git"
            onAction={() => navigate('/history')}
          />
        )}
        {!loading && !error && order ? (
          delivered ? (
            <div className="enjoy-message" role="status">
              <span aria-hidden="true">☕</span>
              <strong>Afiyet olsun</strong>
              <p>Kahveni teslim aldın. İyi günler!</p>
              <button type="button" onClick={() => navigate('/history')}>
                Sipariş Geçmişi
              </button>
            </div>
          ) : (
            <>
              <img src={order.qr_code_data_url} alt="Sipariş QR kodu" />
              <div className={`qr-status status-${order.status.toLowerCase()}`} role="status" aria-live="polite">
                <span className="status-dot" aria-hidden="true"></span>
                <span>{statusLabel}</span>
              </div>
              <p className="qr-note">Durum otomatik olarak güncelleniyor.</p>
            </>
          )
        ) : null}
      </section>
    </main>
  )
}
