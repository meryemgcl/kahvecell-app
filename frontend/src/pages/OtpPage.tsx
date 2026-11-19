import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import client from '../api/client'
import { useAuthStore } from '../store/authStore'
import AuthCard from './AuthCard'
import { useToastStore } from '../store/toastStore'

export default function OtpPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const setTokens = useAuthStore((state) => state.setTokens)
  const setRole = useAuthStore((state) => state.setRole)
  const showToast = useToastStore((state) => state.show)
  const phone = (location.state as { phone?: string } | null)?.phone || ''
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await client.post('/auth/verify-otp', {
        phone_number: phone,
        code,
      })
      setTokens(response.data.access_token, response.data.refresh_token)
      const meResponse = await client.get('/auth/me')
      setRole(meResponse.data.role)
      showToast('Telefon doğrulaması tamamlandı.', 'success')
      navigate(meResponse.data.role === 'SHOP_OWNER' ? '/shop-panel' : '/', { replace: true })
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
              ).response?.data?.detail || 'Kod doğrulanamadı.',
            )
          : 'Kod doğrulanamadı.'
      setError(message)
      showToast(message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard title="Telefonunu doğrula" subtitle={`${phone} numarasına gelen 4 haneli kodu gir.`}>
      <div className="otp-note">
        Test modu: Doğrulama kodu her zaman <strong>1234</strong>.
      </div>
      <form className="auth-form" onSubmit={handleSubmit}>
        <label htmlFor="otp">Doğrulama kodu</label>
        <input
          id="otp"
          className="otp-input"
          inputMode="numeric"
          value={code}
          onChange={(event) =>
            setCode(event.target.value.replace(/\D/g, '').slice(0, 4))
          }
          placeholder="1234"
          pattern="[0-9]{4}"
          maxLength={4}
          required
          autoComplete="one-time-code"
        />
        {error && <p className="form-error" role="alert">{error}</p>}
        <button type="submit" disabled={loading || code.length !== 4}>
          {loading ? 'Doğrulanıyor...' : 'Doğrula'}
        </button>
      </form>
      <p className="auth-link">
        <Link to="/register">Başa dön</Link>
      </p>
    </AuthCard>
  )
}
