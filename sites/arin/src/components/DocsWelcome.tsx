import { useEffect, useState } from 'react'
import '../docs.css'

const docsSections = [
  {
    heading: 'Get Started',
    items: [
      { label: 'Welcome', href: '#welcome', current: true },
      { label: 'Quickstart: Build in 1 min', href: '#quickstart' },
    ],
  },
  {
    heading: 'Arin AI Agent',
    items: [
      { label: 'How Arin works', href: '#how-arin-works' },
      { label: 'Agent modes', href: '#agent-modes' },
      { label: 'Team collaboration', href: '#team-collaboration' },
      { label: 'Chat connectors', href: '#chat-connectors' },
    ],
  },
  {
    heading: 'Build Your App',
    items: [
      { label: 'Branding & SEO', href: '#branding-seo' },
      { label: 'Users & auth', href: '#users-auth' },
      { label: 'Files & media', href: '#files-media' },
      { label: 'Visual editing', href: '#visual-editing' },
    ],
  },
]

const pageSections = [
  { label: 'What can I build with Arin?', href: '#what-can-i-build' },
  { label: 'What features does Arin have?', href: '#what-features-does-arin-have' },
  { label: 'Can Arin support my app as it scales?', href: '#can-arin-scale' },
  { label: 'How do I get started?', href: '#quickstart' },
]

const featureChips = [
  'Workspaces',
  'Prompt builds',
  'Files & Preview',
  'Branding & SEO',
  'Assets',
  'Connectors',
  'Team invites',
  'Version history',
  'Publish',
  'Sandboxed apps',
  'Sessions',
  'Audit history',
]

const assistantPrompts = [
  'How do I publish my first app?',
  'Where do I connect a custom domain?',
  'What is included in the editor?',
]

const searchItems = [
  'Welcome to Arin',
  'Quickstart',
  'How Arin works',
  'Agent modes',
  'Team collaboration',
  'Branding & SEO',
  'Users & Auth',
  'Files & Media',
  'Visual editing',
  'Analytics',
  'Version Control',
]

export function DocsWelcome() {
  const [query, setQuery] = useState('')

  useEffect(() => {
    document.title = 'Arin Docs — Welcome'
  }, [])

  const trimmedQuery = query.trim().toLowerCase()
  const results = trimmedQuery
    ? searchItems.filter((item) => item.toLowerCase().includes(trimmedQuery)).slice(0, 5)
    : []

  return (
    <div className="docs-welcome">
      <div className="docs-welcome__backdrop" aria-hidden="true" />
      <a className="docs-welcome__skip-link" href="#docs-main">Skip to documentation</a>

      <header className="docs-welcome__toolbar">
        <a className="docs-welcome__brand" href="/" aria-label="Arin home">
          <span className="docs-welcome__brand-mark" aria-hidden="true">
            <img src="/assets/logo.svg" alt="" />
          </span>
          <span className="docs-welcome__brand-copy">
            <strong>Arin</strong>
            <span>Docs</span>
          </span>
        </a>

          <nav className="docs-welcome__toolbar-path" aria-label="Documentation path">
            <span>Documentation</span>
            <span aria-hidden="true">/</span>
            <span>Get Started</span>
          </nav>

        <div className="docs-welcome__toolbar-search">
          <label className="docs-welcome__search-field" htmlFor="docs-search">
            <span className="docs-welcome__sr-only">Search Arin documentation</span>
            <svg viewBox="0 0 20 20" aria-hidden="true">
              <path d="M13.7 12.3 17 15.6l-1.4 1.4-3.3-3.3a6 6 0 1 1 1.4-1.4ZM8.5 13A4.5 4.5 0 1 0 8.5 4a4.5 4.5 0 0 0 0 9Z" />
            </svg>
            <input
              id="docs-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search Arin docs"
            />
          </label>

          {trimmedQuery && (
            <div className="docs-welcome__search-results" role="status" aria-live="polite">
              <p id="docs-search-hint">
                {results.length ? `Matching topics for “${query}”` : `No direct matches for “${query}”`}
              </p>
              {results.length > 0 && (
                <ul>
                  {results.map((result) => (
                    <li key={result}>
                      <button type="button">{result}</button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        <div className="docs-welcome__toolbar-actions">
          <a className="docs-welcome__toolbar-link" href="/studio">
            Quickstart
          </a>
          <button className="docs-welcome__assistant-button" type="button">
            Ask Arin
          </button>
        </div>
      </header>

      <div className="docs-welcome__mobile-sections" aria-label="Mobile documentation navigation">
        {docsSections.map((section) => (
          <a key={section.heading} href={section.items[0].href}>
            {section.heading}
          </a>
        ))}
      </div>

      <div className="docs-welcome__layout">
        <aside className="docs-welcome__sidebar" aria-label="Documentation navigation">
          <div className="docs-welcome__sidebar-inner">
            <p className="docs-welcome__sidebar-eyebrow">Navigation</p>

            {docsSections.map((section) => (
              <div className="docs-welcome__nav-group" key={section.heading}>
                <h2>{section.heading}</h2>
                <ul>
                  {section.items.map((item) => (
                    <li key={item.label}>
                      <a
                        className={item.current ? 'is-current' : ''}
                        href={item.href}
                        aria-current={item.current ? 'page' : undefined}
                      >
                        {item.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </aside>

        <main id="docs-main" className="docs-welcome__article-wrap" tabIndex={-1}>
          <article className="docs-welcome__article" aria-labelledby="welcome-title">
            <div className="docs-welcome__hero" id="welcome">
              <div className="docs-welcome__hero-meta">
                <span>Get Started</span>
                <span>Updated August 2, 2026</span>
              </div>
              <h1 id="welcome-title">Welcome to Arin</h1>
              <p className="docs-welcome__lede">
                Arin makes it easy to build useful web apps and websites from a plain-language brief. Create client
                portals, internal tools, marketing sites, and responsive mobile-ready workflows from one workspace.
              </p>
              <p className="docs-welcome__sublede">
                Start with a prompt, shape the result visually, and ship with the infrastructure already wired in.
              </p>
            </div>

            <figure className="docs-welcome__figure">
              <div className="docs-welcome__figure-frame">
                <div className="docs-welcome__figure-badge">
                  <span aria-hidden="true">●</span>
                  Arin editor
                </div>
                <img
                  src="/assets/docs/app-editor.png"
                  alt="Arin app editor showing the AI workspace beside a live preview."
                />
              </div>
              <figcaption>Prompt-driven building, visual editing, and live preview in one workspace.</figcaption>
            </figure>

            <section className="docs-welcome__content-block" id="what-can-i-build">
              <h2>What can I build with Arin?</h2>
              <p>
                You can build working static web apps across common business categories with Arin. Teams can start
                with client dashboards, CRM tools, marketing sites, ops consoles, onboarding portals, and responsive
                mobile-ready workflows without starting from a blank repo.
              </p>
              <p>
                Describe the product in plain language, then refine the generated app with your own content, data
                model, workflows, and brand decisions.
              </p>
            </section>

            <section className="docs-welcome__content-block" id="what-features-does-arin-have">
              <h2>What features does Arin have?</h2>
              <p>
                Arin includes the practical product primitives in this MVP: a workspace, prompt generation, immutable
                files, a safe preview, branding and SEO settings, asset storage, encrypted connector metadata, team
                invites, audit history, and publishing.
              </p>
              <div className="docs-welcome__feature-chips" role="list" aria-label="Key Arin features">
                {featureChips.map((chip) => (
                  <span key={chip} role="listitem">{chip}</span>
                ))}
              </div>
              <p>
                These are the most common building blocks. The rest of the docs expand on how to customize them,
                connect external systems, and move from prototype to team-operated product.
              </p>
            </section>

            <section className="docs-welcome__content-block" id="can-arin-scale">
              <h2>Can Arin support my app as it scales?</h2>
              <p>
                The current Arin slice is designed for teams that need a dependable starting point. It keeps projects
                scoped by workspace, stores immutable versions, and publishes only static sandboxed output. Databases,
                arbitrary server code, and native app-store delivery are future integrations.
              </p>
            </section>

            <section className="docs-welcome__content-block docs-welcome__content-block--callout" id="quickstart">
              <div>
                <p className="docs-welcome__callout-label">Quickstart</p>
                <h2>How do I get started?</h2>
                <p>
                  Build and publish your first Arin app in about a minute. The fastest path is to start with a
                  narrowly scoped prompt, review the generated structure, then polish the app in the editor.
                </p>
              </div>
              <a className="docs-welcome__callout-action" href="#welcome">
                  Open Studio
              </a>
            </section>
          </article>
        </main>

        <aside className="docs-welcome__rail" aria-label="On this page">
          <div className="docs-welcome__rail-card">
            <p>On this page</p>
            <ul>
              {pageSections.map((section) => (
                <li key={section.href}>
                  <a href={section.href}>{section.label}</a>
                </li>
              ))}
            </ul>
          </div>

          <div className="docs-welcome__rail-card docs-welcome__rail-card--assistant">
            <p>Ask Arin docs</p>
            <div className="docs-welcome__assistant-prompts">
              {assistantPrompts.map((prompt) => (
                <button key={prompt} type="button">
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}

export default DocsWelcome
