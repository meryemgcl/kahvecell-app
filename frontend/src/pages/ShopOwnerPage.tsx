import { useEffect, useRef, useState } from 'react'
import { Html5Qrcode } from 'html5-qrcode'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'
import { useToastStore } from '../store/toastStore'
import PageState from '../components/PageState'

type Order = {
  id: string
  status: string
  created_at: string
  customizations: Record<string, unknown> | null
  customer_name?: string | null
  customer_phone?: string | null
  product_name?: string | null
  qr_payload: Record<string, unknown>
}

type TabKey = 'PENDING' | 'ACCEPTED' | 'PREPARING' | 'READY'

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: 'PENDING', label: 'Bekleyen' },
  { key: 'ACCEPTED', label: 'Kabul Edilen' },
  { key: 'PREPARING', label: 'Hazırlanıyor' },
  { key: 'READY', label: 'Hazır' },
]

const actionLabels: Record<TabKey, string> = {
  PENDING: 'Kabul Et',
  ACCEPTED: 'Hazırlamaya Başla',
  PREPARING: 'Hazır',
  READY: 'QR Okut',
}

const nextStatus: Partial<Record<TabKey, string>> = {
  PENDING: 'ACCEPTED',
  ACCEPTED: 'PREPARING',
  PREPARING: 'READY',
}

function formatCustomizations(value: Record<string, unknown> | null) {
  if (!value) return 'Özelleştirme yok'
  return Object.entries(value)
    .filter(([, item]) => item !== false && item !== '')
    .map(([key, item]) => {
      const labels: Record<string, string> = {
        size: 'Boyut',
        milk: 'Süt',
        sugar: 'Şeker',
        extra_shot: 'Ek shot',
      }
      return `${labels[key] || key}: ${typeof item === 'boolean' ? 'Var' : String(item)}`
    })
    .join(' · ')
}

export default function ShopOwnerPage() {
  const navigate = useNavigate()
  const clearTokens = useAuthStore((state) => state.clearTokens)
  const showToast = useToastStore((state) => state.show)
  const [orders, setOrders] = useState<Order[]>([])
  const [activeTab, setActiveTab] = useState<TabKey>('PENDING')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [scannerOrder, setScannerOrder] = useState<Order | null>(null)
  const scannerRef = useRef<Html5Qrcode | null>(null)

  async function loadOrders() {
    try {
      const response = await client.get<Order[]>('/orders/shop/pending')
      setOrders(response.data)
      setError('')
    } catch {
      setError('Siparişler yüklenemedi.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadOrders()
    const interval = window.setInterval(loadOrders, 4000)
    return () => window.clearInterval(interval)
  }, [])

  async function updateStatus(order: Order) {
    const status = nextStatus[order.status as TabKey]
    if (!status) return
    try {
      await client.patch(`/orders/${order.id}/status`, { status })
      await loadOrders()
      showToast('Sipariş durumu güncellendi.', 'success')
    } catch (requestError: unknown) {
      const detail =
        typeof requestError === 'object' && requestError !== null && 'response' in requestError
          ? (
              requestError as {
                response?: { data?: { detail?: string } }
              }
            ).response?.data?.detail
          : null
      setError(detail || 'Sipariş durumu güncellenemedi.')
      showToast(detail || 'Sipariş durumu güncellenemedi.', 'error')
    }
  }

  async function stopScanner() {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop()
      } catch {
        // Scanner may already be stopped.
      }
      scannerRef.current = null
    }
  }

  useEffect(() => {
    if (!scannerOrder) return

    const scanner = new Html5Qrcode('owner-qr-reader')
    scannerRef.current = scanner

    scanner
      .start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        async (decodedText) => {
          try {
            const parsed = JSON.parse(decodedText)
            await client.post(`/orders/${scannerOrder.id}/verify-qr`, {
              qr_payload: parsed,
            })
            await client.patch(`/orders/${scannerOrder.id}/status`, {
              status: 'DELIVERED',
            })
            await stopScanner()
            setScannerOrder(null)
            await loadOrders()
            setError('')
            showToast('QR doğrulandı. Sipariş teslim edildi.', 'success')
          } catch {
            setError('QR kod geçerli değil veya bu siparişe ait değil.')
          }
        },
        () => undefined,
      )
      .catch(() => setError('Kamera açılamadı. Tarayıcı kamera izni verdiğinden emin olun.'))

    return () => {
      stopScanner()
    }
  }, [scannerOrder])

  function logout() {
    clearTokens()
    navigate('/login', { replace: true })
  }

  const filteredOrders = orders.filter((order) => order.status === activeTab)

  return (
    <main className="owner-page">
      <header className="owner-header">
        <div>
          <p className="order-eyebrow">Dükkân Yönetimi</p>
          <h1>Siparişler</h1>
        </div>
        <button type="button" onClick={logout}>Çıkış yap</button>
      </header>

      <nav className="owner-tabs" aria-label="Sipariş durumları">
        {tabs.map((tab) => (
          <button
            type="button"
            key={tab.key}
            className={activeTab === tab.key ? 'active' : ''}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
            <span>{orders.filter((order) => order.status === tab.key).length}</span>
          </button>
        ))}
      </nav>

      {loading && <PageState type="loading" message="Siparişler yükleniyor..." />}
      {!loading && error && (
        <PageState type="error" message={error} onRetry={loadOrders} />
      )}
      {!loading && !error && filteredOrders.length === 0 && (
        <PageState
          type="empty"
          title="Bu sekmede sipariş yok"
          message="Yeni sipariş gelince otomatik olarak burada görünecek."
        />
      )}
      {!loading && !error && filteredOrders.length > 0 && (
        <section className="owner-order-list">
          {filteredOrders.map((order) => (
            <article className="owner-order-card" key={order.id}>
              <div className="owner-order-main">
                <div>
                  <p className="order-eyebrow">
                    {new Date(order.created_at).toLocaleString('tr-TR', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </p>
                  <h2>{order.customer_name || 'Müşteri'}</h2>
                  {order.customer_phone && <p className="customer-phone">{order.customer_phone}</p>}
                </div>
                <div className="owner-product">
                  <strong>{order.product_name || 'Ürün'}</strong>
                  <span>{formatCustomizations(order.customizations)}</span>
                </div>
              </div>
              {order.status === 'READY' ? (
                <button type="button" className="owner-action qr-action" onClick={() => setScannerOrder(order)}>
                  QR Okut
                </button>
              ) : (
                <button type="button" className="owner-action" onClick={() => updateStatus(order)}>
                  {actionLabels[order.status as TabKey]}
                </button>
              )}
            </article>
          ))}
        </section>
      )}

      {scannerOrder && (
        <div className="qr-modal-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget) {
            stopScanner()
            setScannerOrder(null)
          }
        }}>
          <section className="qr-scanner-modal" role="dialog" aria-modal="true">
            <button type="button" className="modal-close" aria-label="Kapat" onClick={() => {
              stopScanner()
              setScannerOrder(null)
            }}>×</button>
            <h2>QR Kodu Okut</h2>
            <div id="owner-qr-reader" className="qr-reader"></div>
            <p>{scannerOrder.customer_name || 'Müşteri'} siparişinin QR kodunu kameraya göster.</p>
          </section>
        </div>
      )}
    </main>
  )
}
