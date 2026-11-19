import type { ReactNode } from 'react'

type AuthCardProps = {
  title: string
  subtitle: string
  children: ReactNode
}

export default function AuthCard({ title, subtitle, children }: AuthCardProps) {
  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="auth-title">
        <div className="brand-mark" aria-hidden="true">☕</div>
        <h1 id="auth-title">{title}</h1>
        <p className="auth-subtitle">{subtitle}</p>
        {children}
      </section>
    </main>
  )
}
