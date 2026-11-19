import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import client from '../api/client'
import PageState from '../components/PageState'

type Product = {
  id: string
  name: string
  description: string | null
  price: number
  is_available: boolean
  category: string | null
}

type ShopDetail = {
  id: string
  name: string
  address: string
  rating: number
  distance_km: number | null
  opening_hours: Record<string, string> | null
  menu: Product[]
}

const categoryNames: Record<string, string[]> = {
  'Espresso Bazlı': ['Espresso', 'Americano', 'Cappuccino', 'Latte'],
  'Filtre Kahveler': ['Filtre Kahve'],
  'Soğuk İçecekler': ['Iced', 'Cold', 'Buzlu', 'Soğuk'],
  'Diğer': [],
}

function getCategory(product: Product) {
  for (const [category, names] of Object.entries(categoryNames)) {
    if (category === 'Diğer') continue
    if (names.some((name) => product.name.toLocaleLowerCase('tr').includes(name.toLocaleLowerCase('tr')))) {
      return category
    }
  }
  return 'Diğer'
}

export default function ShopDetailPage() {
  const { shopId } = useParams()
  const navigate = useNavigate()
  const [shop, setShop] = useState<ShopDetail | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  async function loadShop() {
    if (!shopId) return
    setLoading(true)
    setError('')
    try {
      const response = await client.get<ShopDetail>(`/shops/${shopId}`)
      setShop(response.data)
    } catch {
      setError('Dükkân bilgileri yüklenemedi.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadShop()
  }, [shopId])

  return (
    <main className="detail-page">
      <button className="back-button" type="button" onClick={() => navigate('/')}>
        ← Ana sayfa
      </button>
      {loading && <PageState type="loading" message="Dükkân bilgileri yükleniyor..." />}
      {!loading && error && (
        <PageState type="error" message={error} onRetry={loadShop} />
      )}
      {!loading && !error && shop && shop.menu.length === 0 && (
        <PageState
          type="empty"
          title="Menü henüz hazırlanıyor"
          message="Bu dükkânın menüsü birazdan burada olacak. Başka bir dükkân keşfetmek ister misin?"
          actionLabel="Dükkânlara Dön"
          onAction={() => navigate('/')}
        />
      )}
      {shop && (
        <>
          <header className="detail-header">
            <div>
              <h1>{shop.name}</h1>
              <p>{shop.address}</p>
              {shop.opening_hours && (
                <p className="shop-hours">
                  Hafta içi: {shop.opening_hours.weekdays}
                  {shop.opening_hours.weekend && ` · Hafta sonu: ${shop.opening_hours.weekend}`}
                </p>
              )}
            </div>
            <span className="shop-rating">★ {shop.rating.toFixed(1)}</span>
          </header>
          <section className="menu-list" aria-label="Dükkân menüsü">
            {Object.keys(categoryNames).map((category) => {
              const products = shop.menu.filter((product) => getCategory(product) === category)
              if (products.length === 0) return null
              return (
                <section className="menu-category" key={category}>
                  <h2>{category}</h2>
                  {products.map((product) => (
                    <article className="menu-card" key={product.id}>
                      <div>
                        <h3>{product.name}</h3>
                        {product.description && <p>{product.description}</p>}
                      </div>
                      <div className="menu-card-action">
                        <strong>{product.price.toFixed(2)} TL</strong>
                        <button
                          type="button"
                          disabled={!product.is_available}
                          onClick={() =>
                            navigate(`/shops/${shop.id}/order/${product.id}`, {
                              state: { product, shop },
                            })
                          }
                        >
                          {product.is_available ? 'Sipariş Ver' : 'Tükendi'}
                        </button>
                      </div>
                    </article>
                  ))}
                </section>
              )
            })}
          </section>
        </>
      )}
    </main>
  )
}
