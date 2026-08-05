import { useEffect } from 'react'

type HeaderProps = {
  mobileNavOpen: boolean
  onToggleMobileNav: () => void
}

const navItems = [
  { label: 'Docs', href: '/docs/welcome' },
  { label: 'Studio', href: '/studio' },
  { label: 'Case Studies', href: '#case-studies' },
  { label: 'Pricing', href: '#faq' },
  { label: 'Support', href: '#footer' },
]

export function Header({ mobileNavOpen, onToggleMobileNav }: HeaderProps) {
  useEffect(() => {
    if (!mobileNavOpen) return

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onToggleMobileNav()
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [mobileNavOpen, onToggleMobileNav])

  return (
    <header className="site-header">
      <div className="container header-inner">
        <a className="brand" href="#hero" aria-label="Arin home">
          <span className="brand__mark" aria-hidden="true">
            <img src="/assets/logo.svg" alt="" />
          </span>
          <span className="brand__name">Arin</span>
        </a>

        <nav className="desktop-nav" aria-label="Primary navigation">
          {navItems.map((item) => (
            <a key={item.href} href={item.href}>
              {item.label}
            </a>
          ))}
        </nav>

        <div className="header-actions">
          <a className="button button--soft button--compact" href="/auth?mode=login&next=/studio">
            Log in
          </a>
          <a className="button button--primary button--compact" href="/auth?mode=register&next=/studio">
            Create account
          </a>
        </div>

        <button
          className="mobile-menu-button"
          type="button"
          aria-expanded={mobileNavOpen}
          aria-controls="mobile-navigation"
          aria-label={mobileNavOpen ? 'Close navigation' : 'Open navigation'}
          onClick={onToggleMobileNav}
        >
          <span />
          <span />
          <span />
        </button>
      </div>

      {mobileNavOpen && (
        <nav id="mobile-navigation" className="mobile-nav" aria-label="Mobile navigation">
          {navItems.map((item) => (
            <a key={item.href} href={item.href} onClick={onToggleMobileNav}>
              {item.label}
              <span aria-hidden="true">↗</span>
            </a>
          ))}
          <a href="/auth?mode=login&next=/studio" onClick={onToggleMobileNav}>
            Log in
            <span aria-hidden="true">↗</span>
          </a>
        </nav>
      )}
    </header>
  )
}
