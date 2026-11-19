import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'
import { useToastStore } from '../store/toastStore'
import PageState from '../components/PageState'

type Subscription = {
  id: string
  plan_type: 'STARTER' | 'PREMIUM' | 'UNLIMITED'
  remaining_credits: number
  status: string
  started_at: string
  expires_at: string
}

type Plan = {
  plan_type: 'STARTER' | 'PREMIUM' | 'UNLIMITED'
  name: string
  monthly_price: number
  monthly_credits: number
  guest_credits: number
  priority_support: boolean
}

const planNames: Record<string, string> = {
  STARTER: 'Starter',
  PREMIUM: 'Premium',
  UNLIMITED: 'Unlimited',
}

export default function SubscriptionPage() {
  const navigate = useNavigate()
  const showToast = useToastStore((state) => state.show)
  const [active, setActive] = useState<Subscription | null>(null)
  const [plans, setPlans] = useState<Plan[]>([])
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null)
  const [cardNumber] = useState('4242-4242-4242-4242')
  const [loading, setLoading] = useState(true)
  const [paying, setPaying] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [plansError, setPlansError] = useState('')

  async function loadSubscription() {
    try {
      const response = await client.get<Subscription>('/subscriptions/me')
      setActive(response.data)
    } catch {
      setActive(null)
    }
  }

  useEffect(() => {
    loadPage()
  }, [])

  async function loadPage() {
    setLoading(true)
    setPlansError('')
    try {
      await Promise.all([
        loadSubscription(),
        client
          .get<Plan[]>('/subscriptions/plans')
          .then((response) => setPlans(response.data))
          .catch(() => {
            setPlans([])
            setPlansError('Paketler yüklenemedi.')
          }),
      ])
    } finally {
      setLoading(false)
    }
  }

  async function submitPurchase(event: FormEvent) {
    event.preventDefault()
    if (!selectedPlan) return

    setPaying(true)
    setNotice('')
    setError('')
    try {
      const body = {
        plan_type: selectedPlan.plan_type,
        card_token: cardNumber,
      }
      const response = active
        ? await client.patch<Subscription>('/subscriptions/me', body)
        : await client.post<Subscription>('/subscriptions', body)

      setActive(response.data)
      setSelectedPlan(null)
      setNotice(`${planNames[response.data.plan_type]} paketiniz başarıyla aktif edildi.`)
      showToast(`${planNames[response.data.plan_type]} paketiniz başarıyla aktif edildi.`, 'success')
    } catch (requestError: unknown) {
      let message = 'Ödeme başarısız oldu.'
      if (typeof requestError === 'object' && requestError !== null && 'response' in requestError) {
        const detail = (
          requestError as {
            response?: { data?: { detail?: unknown } }
          }
        ).response?.data?.detail
        if (typeof detail === 'string') message = detail
      }
      setError(message)
      showToast(message, 'error')
    } finally {
      setPaying(false)
    }
  }

  async function cancelSubscription() {
    setNotice('')
    setError('')
    try {
      await client.delete('/subscriptions/me')
      setActive(null)
      setNotice('Aboneliğiniz iptal edildi.')
    } catch {
      setError('Abonelik iptal edilemedi.')
    }
  }

  function formatDate(value: string) {
    return new Date(value).toLocaleDateString('tr-TR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })
  }

  return (
    <main className="subscription-page">
      <header className="history-header">
        <button className="back-button" type="button" onClick={() => navigate('/')}>
          ← Ana sayfa
        </button>
        <h1>Abonelik</h1>
      </header>

      {notice && <div className="subscription-notice notice-success" role="status">{notice}</div>}
      {error && <div className="subscription-notice notice-error" role="alert">{error}</div>}

      <section className="current-subscription" aria-labelledby="active-plan-title">
        <p className="order-eyebrow">Mevcut abonelik</p>
        {loading ? (
          <p>Abonelik bilgisi yükleniyor...</p>
        ) : active ? (
          <div className="active-plan">
            <div>
              <h2 id="active-plan-title">{planNames[active.plan_type] || active.plan_type}</h2>
              <p>
                {active.plan_type === 'UNLIMITED'
                  ? 'Kalan kredi: Sınırsız'
                  : `Kalan kredi: ${active.remaining_credits}`}
              </p>
              <p>Bitiş tarihi: {formatDate(active.expires_at)}</p>
            </div>
            <button type="button" className="cancel-button" onClick={cancelSubscription}>
              İptal Et
            </button>
          </div>
        ) : (
          <div className="no-subscription">
            <h2 id="active-plan-title">Aktif aboneliğiniz yok</h2>
            <p>Bir paket satın alarak KahveCell siparişlerine başlayabilirsin.</p>
          </div>
        )}
      </section>

      <section className="plan-grid" aria-label="Abonelik paketleri">
        {loading && <PageState type="loading" message="Abonelik paketleri yükleniyor..." />}
        {!loading && plansError && (
          <PageState type="error" message={plansError} onRetry={loadPage} />
        )}
        {!loading && !plansError && plans.length === 0 && (
          <PageState
            type="empty"
            title="Paket bulunamadı"
            message="Şu an satışta paket yok. Biraz sonra tekrar kontrol edebilirsin."
          />
        )}
        {!loading && !plansError && plans.map((plan) => (
          <article className="plan-card" key={plan.plan_type}>
            <p className="order-eyebrow">{plan.name}</p>
            <h2>{plan.monthly_price.toFixed(2)} TL <span>/ ay</span></h2>
            <ul>
              <li>
                {plan.monthly_credits === -1
                  ? 'Sınırsız kahve'
                  : `${plan.monthly_credits} kahve hakkı / ay`}
              </li>
              {plan.guest_credits > 0 && <li>{plan.guest_credits} misafir hakkı</li>}
              {plan.priority_support && <li>Öncelikli sipariş</li>}
              {plan.guest_credits === 0 && !plan.priority_support && <li>Tüm dükkânlarda geçerli</li>}
            </ul>
            <button type="button" onClick={() => {
              setSelectedPlan(plan)
              setNotice('')
              setError('')
            }}>
              {active ? 'Paket Değiştir' : 'Satın Al'}
            </button>
          </article>
        ))}
      </section>

      {selectedPlan && (
        <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
          if (event.target === event.currentTarget) setSelectedPlan(null)
        }}>
          <section className="payment-modal" role="dialog" aria-modal="true" aria-labelledby="payment-title">
            <button
              type="button"
              className="modal-close"
              aria-label="Pencereyi kapat"
              onClick={() => setSelectedPlan(null)}
            >
              ×
            </button>
            <p className="order-eyebrow">Ödeme</p>
            <h2 id="payment-title">{selectedPlan.name} — {selectedPlan.monthly_price.toFixed(2)} TL</h2>
            <form onSubmit={submitPurchase}>
              <label htmlFor="cardNumber">Kart numarası</label>
              <input
                id="cardNumber"
                value={cardNumber}
                readOnly
                aria-describedby="test-card-note"
              />
              <p id="test-card-note" className="test-card-note">
                Test kartı, değiştirmeyin
              </p>
              {error && <p className="form-error" role="alert">{error}</p>}
              <button type="submit" disabled={paying}>
                {paying ? 'Ödeme işleniyor...' : 'Ödemeyi Onayla'}
              </button>
            </form>
          </section>
        </div>
      )}
    </main>
  )
}
