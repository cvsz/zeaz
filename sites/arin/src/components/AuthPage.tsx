import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError, api } from '../api'
import { safeAuthRedirect } from '../security'

type AuthMode = 'login' | 'register'

export function AuthPage() {
  const initialMode = new URLSearchParams(window.location.search).get('mode') === 'register' ? 'register' : 'login'
  const [mode, setMode] = useState<AuthMode>(initialMode)
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    document.title = mode === 'login' ? 'Log in — Arin' : 'Create your Arin account'
  }, [mode])

  const heading = useMemo(
    () => mode === 'login' ? 'Welcome back to Arin' : 'Build your first app with Arin',
    [mode],
  )

  function switchMode(nextMode: AuthMode) {
    setMode(nextMode)
    setStatus('')
    setError('')
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError('')
    setStatus('')
    try {
      if (mode === 'register') await api.register(email, name, password)
      await api.login(email, password)
      window.location.assign(safeAuthRedirect(new URLSearchParams(window.location.search).get('next')))
    } catch (caught) {
      const message = caught instanceof ApiError ? caught.message : 'We could not complete that request.'
      setError(message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page" aria-labelledby="auth-title">
      <div className="auth-page__glow" aria-hidden="true" />
      <a className="auth-page__brand" href="/" aria-label="Arin home">
        <span className="brand__mark" aria-hidden="true"><img src="/assets/logo.svg" alt="" /></span>
        <span>Arin</span>
      </a>

      <section className="auth-card">
        <div className="auth-card__eyebrow"><span aria-hidden="true">✦</span> AI app builder for business</div>
        <h1 id="auth-title">{heading}</h1>
        <p className="auth-card__lede">
          {mode === 'login'
            ? 'Open your workspace and keep building where you left off.'
            : 'Start with a prompt, then shape, preview, and publish a working app.'}
        </p>

        <div className="auth-switcher" role="tablist" aria-label="Account access">
          <button type="button" role="tab" aria-selected={mode === 'login'} className={mode === 'login' ? 'is-active' : ''} onClick={() => switchMode('login')}>
            Log in
          </button>
          <button type="button" role="tab" aria-selected={mode === 'register'} className={mode === 'register' ? 'is-active' : ''} onClick={() => switchMode('register')}>
            Create account
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === 'register' && (
            <label>
              <span>Your name</span>
              <input value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" required minLength={1} maxLength={120} />
            </label>
          )}
          <label>
            <span>Email</span>
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required maxLength={320} />
          </label>
          <label>
            <span>Password</span>
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required minLength={12} />
            {mode === 'register' && <small>Use at least 12 characters.</small>}
          </label>
          <button className="button button--primary auth-form__submit" type="submit" disabled={busy}>
            {busy ? 'Working…' : mode === 'login' ? 'Open workspace' : 'Create account'}
            <span aria-hidden="true">→</span>
          </button>
        </form>

        <p className="auth-status" role="status" aria-live="polite">{status}</p>
        {error && <p className="form-error" role="alert">{error}</p>}
        <p className="auth-card__footnote">Your workspace data stays behind an encrypted session and scoped project permissions.</p>
      </section>
    </main>
  )
}
