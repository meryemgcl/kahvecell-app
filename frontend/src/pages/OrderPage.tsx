import { useEffect, useState, type FormEvent } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import client from '../api/client'
import { useToastStore } from '../store/toastStore'
import PageState from '../components/PageState'

type Product = {
  id: string
  name: string
  description: string | null
  price: number
  is_available: boolean
}

type Shop = {
  id: string
  name: string
  address: string
  opening_hours?: Record<string, string> | null
}

type Subscription = {
  id: string
  plan_type: string
  remaining_credits: number
  status: string
}

export default function OrderPage() {
  const { shopId, productId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const showToast = useToastStore((state) => state.show)
  const routeState = location.state as { product?: Product; shop?: Shop } | null
  const [product, setProduct] = useState<Product | null>(routeState?.product || null)
  const [shop, setShop] = useState<Shop | null>(routeState?.shop || null)
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [size, setSize] = useState('M')
  const [milk, setMilk] = useState('Normal')
  const [sugar, setSugar] = useState('Orta')
  const [extraShot, setExtraShot] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [loadingData, setLoadingData] = useState(true)
  const [dataError, setDataError] = useState('')

  async function loadOrderData() {
    setLoadingData(true)
    setDataError('')
    try {
      try {
        const subscriptionResponse = await client.get<Subscription>('/subscriptions/me')
        setSubscription(subscriptionResponse.data)
      } catch {
        setSubscription(null)
      }
      if (!shop && shopId) {
        const shopResponse = await client.get<Shop>(`/shops/${shopId}`)
        setShop(shopResponse.data)
      }
      if (!product && shopId && productId) {
        const menuResponse = await client.get<Product[]>(`/shops/${shopId}/menu`)
        setProduct(menuResponse.data.find((item) => item.id === productId) || null)
      }
    } catch (requestError: unknown) {
      setDataError('Sipariş ekranı yüklenemedi.')
    } finally {
      setLoadingData(false)
    }
  }

  useEffect(() => {
    loadOrderData()
  }, [product, productId, shop, shopId])

  const unlimited = subscription?.plan_type === 'UNLIMITED'
  const canOrder =
    subscription?.status === 'ACTIVE' &&
    (unlimited || (subscription.remaining_credits > 0 && subscription.remaining_credits !== -1))
  const remainingAfter =
    subscription && unlimited
      ? 'Sınırsız'
      : subscription
        ? Math.max(0, subscription.remaining_credits - 1)
        : 0

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!canOrder || !shopId || !productId) return

    setLoading(true)
    setError('')
    try {
      const response = await client.post('/orders', {
        shop_id: shopId,
        product_id: productId,
        customizations: {
          size,
          milk,
          sugar,
          extra_shot: extraShot,
        },
      })
      navigate(`/orders/${response.data.id}/qr`, {
        state: { order: response.data },
      })
      showToast('Siparişiniz başarıyla oluşturuldu.', 'success')
    } catch (requestError: unknown) {
      const message =
        typeof requestError === 'object' &&
        requestError !== null &&
        'response' in requestError
          ? String(
              (
                requestError as {
                  response?: { data?: { detail?: string } }
                }
              ).response?.data?.detail || 'Sipariş oluşturulamadı.',
            )
          : 'Sipariş oluşturulamadı.'
      setError(message)
      showToast(message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="order-page">
      <button className="back-button" type="button" onClick={() => navigate(-1)}>
        ← Geri
      </button>

      {loadingData && <PageState type="loading" message="Sipariş bilgileri yükleniyor..." />}
      {!loadingData && dataError && (
        <PageState type="error" message={dataError} onRetry={loadOrderData} />
      )}
      {!loadingData && !dataError && !product && (
        <PageState
          type="empty"
          title="Ürün bulunamadı"
          message="Menüden tekrar bir kahve seçebilirsin."
          actionLabel="Menüye Dön"
          onAction={() => navigate(`/shops/${shopId}`)}
        />
      )}

      {!loadingData && !dataError && product && (
      <section className="order-card">
        <div className="order-heading">
          <div>
            <p className="order-eyebrow">{shop?.name || 'Dükkân'}</p>
            <h1>{product?.name || 'Ürün yükleniyor...'}</h1>
            {product?.description && <p>{product.description}</p>}
          </div>
          {product && <strong className="order-price">{product.price.toFixed(2)} TL</strong>}
        </div>

        <form className="order-form" onSubmit={handleSubmit}>
          <fieldset>
            <legend>Boyut</legend>
            <div className="option-row">
              {['S', 'M', 'L'].map((option) => (
                <label key={option}>
                  <input type="radio" name="size" value={option} checked={size === option} onChange={() => setSize(option)} />
                  {option}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend>Süt tipi</legend>
            <select value={milk} onChange={(event) => setMilk(event.target.value)}>
              <option>Normal</option>
              <option>Az sütlü</option>
              <option>Yulaf sütü</option>
              <option>Süssüz</option>
            </select>
          </fieldset>

          <fieldset>
            <legend>Şeker</legend>
            <select value={sugar} onChange={(event) => setSugar(event.target.value)}>
              <option>Şekersiz</option>
              <option>Az</option>
              <option>Orta</option>
              <option>Şekerli</option>
            </select>
          </fieldset>

          <label className="checkbox-option">
            <input type="checkbox" checked={extraShot} onChange={(event) => setExtraShot(event.target.checked)} />
            Ek shot
          </label>

          <div className={`credit-box ${canOrder ? '' : 'credit-warning'}`}>
            {subscription ? (
              <>
                <strong>{unlimited ? 'Sınırsız paket' : `Kalan kredi: ${subscription.remaining_credits}`}</strong>
                <span>
                  {unlimited
                    ? 'Bu siparişten sonra kredi değişmez.'
                    : `Bu sipariş sonrası: ${remainingAfter} kredi kalacak`}
                </span>
              </>
            ) : (
              <>
                <strong>Aktif abonelik bulunamadı</strong>
                <span>Sipariş vermek için paket satın almalısın.</span>
              </>
            )}
          </div>

          {error && <p className="form-error" role="alert">{error}</p>}
          {canOrder ? (
            <button className="order-confirm" type="submit" disabled={loading || !product}>
              {loading ? 'Sipariş oluşturuluyor...' : 'Siparişi Onayla'}
            </button>
          ) : (
            <button className="order-confirm" type="button" onClick={() => navigate('/subscriptions')}>
              Abonelik Sayfasına Git
            </button>
          )}
        </form>
      </section>
      )}
    </main>
  )
}
