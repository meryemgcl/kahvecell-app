import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'
import AuthCard from './AuthCard'
import { useToastStore } from '../store/toastStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const setTokens = useAuthStore((state) => state.setTokens)
  const setRole = useAuthStore((state) => state.setRole)
  const showToast = useToastStore((state) => state.show)
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await client.post('/auth/login', {
        phone_number: phone,
        password,
      })
      setTokens(response.data.access_token, response.data.refresh_token)
      const meResponse = await client.get('/auth/me')
      setRole(meResponse.data.role)
      if (meResponse.data.role === 'SHOP_OWNER') {
        showToast('Dükkân sahibi paneline hoş geldiniz.', 'success')
        navigate('/shop-panel', { replace: true })
      } else {
        showToast('Giriş başarılı.', 'success')
        navigate('/', { replace: true })
      }
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
              ).response?.data?.detail || 'Giriş yapılamadı.',
            )
          : 'Giriş yapılamadı.'
      setError(message)
      showToast(message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard title="Tekrar hoş geldin" subtitle="Kahve yolculuğuna devam et.">
      <form className="auth-form" onSubmit={handleSubmit}>
        <label htmlFor="phone">Telefon numarası</label>
        <input
          id="phone"
          type="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          placeholder="05XX XXX XX XX"
          required
        />

        <label htmlFor="password">Şifre</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        {error && <p className="form-error" role="alert">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Giriş yapılıyor...' : 'Giriş yap'}
        </button>
      </form>
      <p className="auth-link">
        Hesabın yok mu? <Link to="/register">Hemen kayıt ol</Link>
      </p>
    </AuthCard>
  )
}
