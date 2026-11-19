import { useEffect, useMemo, useState } from 'react'
import { divIcon, type LatLngExpression } from 'leaflet'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import { useNavigate } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'
import PageState from '../components/PageState'

type Location = {
  lat: number
  lng: number
}

type Shop = {
  id: string
  name: string
  address: string
  latitude: number
  longitude: number
  rating: number
  distance_km: number | null
  is_active: boolean
}

const ANKARA_KIZILAY: Location = { lat: 39.9208, lng: 32.8541 }

const shopIcon = divIcon({
  className: 'kahvecell-marker',
  html: '<span class="shop-marker">☕</span>',
  iconSize: [36, 36],
  iconAnchor: [18, 36],
  popupAnchor: [0, -34],
})

const userIcon = divIcon({
  className: 'kahvecell-marker',
  html: '<span class="user-marker"></span>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
  popupAnchor: [0, -10],
})

function RecenterMap({ location }: { location: Location }) {
  const map = useMap()

  useEffect(() => {
    map.setView([location.lat, location.lng], 13)
  }, [location, map])

  return null
}

export default function HomePage() {
  const navigate = useNavigate()
  const clearTokens = useAuthStore((state) => state.clearTokens)
  const [location, setLocation] = useState<Location>(ANKARA_KIZILAY)
  const [locationLabel, setLocationLabel] = useState('Ankara Kızılay varsayılan konumu')
  const [shops, setShops] = useState<Shop[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationLabel('Konum bulunamadı; Ankara Kızılay kullanılıyor')
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        })
        setLocationLabel('Bulunduğun konum')
      },
      () => {
        setLocation(ANKARA_KIZILAY)
        setLocationLabel('Konum izni verilmedi; Ankara Kızılay kullanılıyor')
      },
      { enableHighAccuracy: true, timeout: 8000 },
    )
  }, [])

  useEffect(() => {
    let active = true

    async function loadShops() {
      setLoading(true)
      setError('')
      try {
        const response = await client.get<Shop[]>('/shops', {
          params: {
            lat: location.lat,
            lng: location.lng,
            radius: 100,
          },
        })
        if (active) setShops(response.data)
      } catch {
        if (active) setError('Dükkânlar yüklenemedi.')
      } finally {
        if (active) setLoading(false)
      }
    }

    loadShops()
    return () => {
      active = false
    }
  }, [location])

  const filteredShops = useMemo(() => {
    const term = search.trim().toLocaleLowerCase('tr')
    if (!term) return shops
    return shops.filter(
      (shop) =>
        shop.name.toLocaleLowerCase('tr').includes(term) ||
        shop.address.toLocaleLowerCase('tr').includes(term),
    )
  }, [search, shops])

  function logout() {
    clearTokens()
    navigate('/login', { replace: true })
  }

  const mapCenter: LatLngExpression = [location.lat, location.lng]

  return (
    <main className="home-page">
      <header className="home-header">
        <button className="home-brand" type="button" onClick={() => navigate('/')}>
          <span aria-hidden="true">☕</span> KahveCell
        </button>
        <nav className="header-nav" aria-label="Ana menü">
          <button type="button" onClick={() => navigate('/subscriptions')}>Abonelik</button>
          <button type="button" onClick={() => navigate('/history')}>Geçmiş</button>
          <button className="header-logout" type="button" onClick={logout}>Çıkış yap</button>
        </nav>
      </header>

      <div className="home-toolbar">
        <div>
          <h1>Yakındaki kahve dükkânları</h1>
          <p>{locationLabel}</p>
        </div>
        <input
          className="shop-search"
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="İsim veya adres ara"
          aria-label="Dükkân ara"
        />
      </div>

      <div className="home-content">
        <section className="shop-list" aria-label="Dükkân listesi">
          {loading && <PageState type="loading" message="Yakındaki dükkânlar yükleniyor..." />}
          {!loading && error && (
            <PageState type="error" message={error} onRetry={() => setLocation({ ...location })} />
          )}
          {!loading && !error && filteredShops.length === 0 && (
            <PageState
              type="empty"
              title={search ? 'Aramana uygun dükkân yok' : 'Yakında dükkân yok'}
              message={search ? 'Farklı bir isim veya adres dene.' : 'Konumunu kontrol edip tekrar arayabilirsin.'}
              actionLabel={search ? 'Aramayı Temizle' : 'Tekrar Ara'}
              onAction={() => search ? setSearch('') : setLocation({ ...location })}
            />
          )}

          {!loading &&
            filteredShops.map((shop) => (
              <article className="shop-card" key={shop.id}>
                <div className="shop-card-heading">
                  <h2>{shop.name}</h2>
                  <span className="shop-rating" aria-label={`Puan ${shop.rating}`}>
                    ★ {shop.rating.toFixed(1)}
                  </span>
                </div>
                <p className="shop-address">{shop.address}</p>
                <div className="shop-card-footer">
                  <span>
                    {shop.distance_km === null
                      ? 'Mesafe hesaplanmadı'
                      : `${shop.distance_km.toFixed(1)} km uzakta`}
                  </span>
                  <button
                    type="button"
                    onClick={() => navigate(`/shops/${shop.id}`)}
                  >
                    Menüyü Gör
                  </button>
                </div>
              </article>
            ))}
        </section>

        <section className="shop-map" aria-label="Dükkân haritası">
          <MapContainer
            center={mapCenter}
            zoom={13}
            scrollWheelZoom
            className="leaflet-map"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <RecenterMap location={location} />
            <Marker position={[location.lat, location.lng]} icon={userIcon}>
              <Popup>Senin konumun</Popup>
            </Marker>
            {filteredShops.map((shop) => (
              <Marker
                key={shop.id}
                position={[shop.latitude, shop.longitude]}
                icon={shopIcon}
              >
                <Popup>
                  <strong>{shop.name}</strong>
                  <br />
                  {shop.address}
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </section>
      </div>
    </main>
  )
}
