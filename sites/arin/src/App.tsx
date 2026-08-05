import { useState } from 'react'
import { categories } from './data'
import { BuildWalkthrough } from './components/BuildWalkthrough'
import { CapabilitiesGrid } from './components/CapabilitiesGrid'
import { CaseStudyRail } from './components/CaseStudyRail'
import { FaqAccordion } from './components/FaqAccordion'
import { Footer } from './components/Footer'
import { Header } from './components/Header'
import { HeroBuilder } from './components/HeroBuilder'
import { ProductMockups } from './components/ProductMockups'
import { Testimonials } from './components/Testimonials'
import { DocsWelcome } from './components/DocsWelcome'
import { AuthPage } from './components/AuthPage'
import { StudioPage } from './components/StudioPage'

function HomePage() {
  const [activeCategory, setActiveCategory] = useState(categories[0].id)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  return (
    <div className="site-shell">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <Header mobileNavOpen={mobileNavOpen} onToggleMobileNav={() => setMobileNavOpen((open) => !open)} />
      <main id="main-content" tabIndex={-1} aria-label="Arin homepage replica">
        <HeroBuilder activeCategory={activeCategory} onCategoryChange={setActiveCategory} />
        <CaseStudyRail />
        <BuildWalkthrough />
        <CapabilitiesGrid />
        <ProductMockups />
        <Testimonials />
        <FaqAccordion openIndex={openFaq} onToggle={(index) => setOpenFaq((current) => (current === index ? null : index))} />
        <Footer />
      </main>
    </div>
  )
}

export default function App() {
  const pathname = window.location.pathname.replace(/\/+$/, '') || '/'

  if (pathname === '/auth') {
    return <AuthPage />
  }

  if (pathname === '/studio' || pathname.startsWith('/studio/')) {
    return <StudioPage />
  }

  if (pathname === '/docs/welcome' || pathname.startsWith('/docs/')) {
    return <DocsWelcome />
  }

  return <HomePage />
}
