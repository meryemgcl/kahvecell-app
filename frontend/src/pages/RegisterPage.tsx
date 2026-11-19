import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import client from '../api/client'
import AuthCard from './AuthCard'
import { useToastStore } from '../store/toastStore'

export default function RegisterPage() {
  const navigate = useNavigate()
  const showToast = useToastStore((state) => state.show)
  const [phone, setPhone] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      await client.post('/auth/register', {
        phone_number: phone,
        full_name: fullName,
        password,
      })
      navigate('/otp', { state: { phone } })
      showToast('OTP doğrulama ekranına yönlendiriliyorsunuz.', 'success')
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
              ).response?.data?.detail || 'Kayıt yapılamadı.',
            )
          : 'Kayıt yapılamadı.'
      setError(message)
      showToast(message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard title="KahveCell'e katıl" subtitle="Hesabını birkaç saniyede oluştur.">
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

        <label htmlFor="fullName">Ad soyad</label>
        <input
          id="fullName"
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
          placeholder="Adın Soyadın"
          required
        />

        <label htmlFor="password">Şifre</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="En az 6 karakter"
          minLength={6}
          required
        />

        {error && <p className="form-error" role="alert">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? 'Gönderiliyor...' : 'Kayıt ol'}
        </button>
      </form>
      <p className="auth-link">
        Zaten hesabın var mı? <Link to="/login">Giriş yap</Link>
      </p>
    </AuthCard>
  )
}
