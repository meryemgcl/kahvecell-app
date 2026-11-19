import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'
import PageState from '../components/PageState'

type Order = {
  id: string
  status: string
  created_at: string
  shop_name?: string | null
  product_name?: string | null
}

const statusLabels: Record<string, string> = {
  PENDING: 'Bekliyor',
  ACCEPTED: 'Kabul Edildi',
  PREPARING: 'Hazırlanıyor',
  READY: 'Hazır',
  DELIVERED: 'Teslim Edildi',
  CANCELLED: 'İptal Edildi',
}

export default function HistoryPage() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function loadHistory() {
    setLoading(true)
    setError('')
    try {
      const response = await client.get<Order[]>('/orders/history')
      setOrders(response.data)
    } catch {
      setError('Sipariş geçmişi yüklenemedi.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  return (
    <main className="history-page">
      <header className="history-header">
        <button className="back-button" type="button" onClick={() => navigate('/')}>
          ← Ana sayfa
        </button>
        <h1>Sipariş Geçmişi</h1>
      </header>

      {loading && <PageState type="loading" message="Sipariş geçmişin yükleniyor..." />}
      {!loading && error && (
        <PageState type="error" message={error} onRetry={loadHistory} />
      )}
      {!loading && !error && orders.length === 0 && (
        <PageState
          type="empty"
          title="Henüz siparişin yok"
          message="Yakındaki bir dükkânı seçip ilk kahveni verebilirsin."
          actionLabel="Dükkânları Keşfet"
          onAction={() => navigate('/')}
        />
      )}

      {!loading && orders.length > 0 && (
        <section className="history-list" aria-label="Sipariş geçmişi">
          {orders.map((order) => (
            <article className="history-row" key={order.id}>
              <div className="history-date">
                <strong>
                  {new Date(order.created_at).toLocaleDateString('tr-TR', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })}
                </strong>
                <span>
                  {new Date(order.created_at).toLocaleTimeString('tr-TR', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
              <div className="history-product">
                <strong>{order.product_name || 'Ürün'}</strong>
                <span>{order.shop_name || 'Dükkân'}</span>
              </div>
              <button
                type="button"
                className={`history-status status-${order.status.toLowerCase()}`}
                onClick={() => navigate(`/orders/${order.id}/qr`)}
              >
                {statusLabels[order.status] || order.status}
              </button>
            </article>
          ))}
        </section>
      )}
    </main>
  )
}
