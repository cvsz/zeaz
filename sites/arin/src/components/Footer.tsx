export function Footer() {
  return (
    <footer id="footer" className="site-footer">
      <div className="container">
        <div className="footer-cta">
          <div>
            <p className="eyebrow">START BUILDING FOR FREE</p>
            <h2>Make your next idea real.</h2>
            <p>No credit card required. Describe your idea and start building in seconds.</p>
          </div>
          <form className="footer-prompt" onSubmit={(event) => event.preventDefault()}>
            <label className="sr-only" htmlFor="footer-prompt-input">Describe your idea</label>
            <input id="footer-prompt-input" placeholder="Build a CRM for my regional HVAC company" />
            <button type="submit">Build it <span aria-hidden="true">→</span></button>
          </form>
        </div>
        <div className="footer-main">
          <a className="brand" href="#hero" aria-label="Arin home">
            <span className="brand__mark" aria-hidden="true"><img src="/assets/logo.svg" alt="" /></span>
            <span className="brand__name">Arin</span>
          </a>
          <p>The best AI app and website builder for business.</p>
          <div className="footer-links">
            <div><strong>Product</strong><a href="#capabilities">Features</a><a href="#scale">Pricing</a><a href="#build-flow">How it works</a></div>
            <div><strong>Company</strong><a href="#case-studies">Case studies</a><a href="#testimonials">Customers</a><a href="/docs/welcome">Docs</a></div>
            <div><strong>Legal</strong><a href="#footer">Terms of Service</a><a href="#footer">Privacy Policy</a><a href="#footer">Abuse</a></div>
            <div><strong>Connect</strong><a href="#footer">Support</a><a href="#footer">Status</a><a href="#footer">Community</a></div>
          </div>
        </div>
        <div className="footer-bottom"><span>© 2026 Arin. All rights reserved.</span><span>Made for people building what is next.</span></div>
      </div>
    </footer>
  )
}
