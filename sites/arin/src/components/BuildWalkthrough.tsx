import { SectionHeading, Reveal } from './ui'

const buildSteps = [
  { label: 'Creating contacts and accounts', icon: '◎', state: 'done' },
  { label: 'Built opportunities section', icon: '◌', state: 'done' },
  { label: 'Added role based access control', icon: '◇', state: 'done' },
  { label: 'Published', icon: '✓', state: 'active' },
]

export function BuildWalkthrough() {
  return (
    <section id="build-flow" className="section walkthrough-section" aria-labelledby="walkthrough-title">
      <div className="container">
        <SectionHeading
          eyebrow="FROM IDEA TO PUBLISHED APP IN MINUTES"
          title={<span id="walkthrough-title">Build by <em className="gradient-text">chatting</em></span>}
          description="Describe what you want. Arin builds it in real time."
        />

        <div className="walkthrough-grid">
          <Reveal className="chat-panel" delay={120}>
            <div className="chat-panel__topline">
              <span className="status-dot" />
              <span>Arin is building your CRM</span>
              <span className="chat-panel__dots" aria-hidden="true">•••</span>
            </div>
            <div className="chat-panel__message">
              <p>Build a CRM for my 75 person sales team</p>
            </div>
            <div className="chat-panel__activity">
              {buildSteps.map((step) => (
                <div className={`activity-row activity-row--${step.state}`} key={step.label}>
                  <span className="activity-row__icon" aria-hidden="true">{step.icon}</span>
                  <span>{step.label}</span>
                  <span className="activity-row__check" aria-hidden="true">{step.state === 'active' ? '…' : '✓'}</span>
                </div>
              ))}
            </div>
            <div className="chat-panel__ready">
              <span className="ready-icon" aria-hidden="true">✦</span>
              <div>
                <strong>Your CRM is ready</strong>
                <span>Preview and publish your new app</span>
              </div>
              <button type="button">Open <span aria-hidden="true">↗</span></button>
            </div>
          </Reveal>

          <Reveal className="browser-mockup" delay={220}>
            <div className="browser-mockup__chrome">
              <div className="window-dots" aria-hidden="true"><i /><i /><i /></div>
              <span>app.arin.ai / sales</span>
              <span className="browser-mockup__live"><i /> Live</span>
            </div>
            <div className="browser-mockup__body">
              <aside className="mock-sidebar">
                <div className="mock-brand"><span aria-hidden="true">ϟ</span> Sales CRM</div>
                <div className="mock-nav-item mock-nav-item--active">▦ Overview</div>
                <div className="mock-nav-item">♧ Contacts</div>
                <div className="mock-nav-item">◇ Opportunities</div>
                <div className="mock-nav-item">◌ Tasks</div>
                <div className="mock-nav-item">⚙ Settings</div>
              </aside>
              <div className="mock-main">
                <div className="mock-main__heading"><span>Overview</span><button type="button">+ New deal</button></div>
                <div className="mock-metrics">
                  <div><span>Active Deals</span><b>128</b><small>+8%</small></div>
                  <div><span>Win Rate</span><b>42%</b><small>+4%</small></div>
                  <div><span>Avg Deal</span><b>$89k</b><small>+6%</small></div>
                </div>
                <div className="mock-chart">
                  <div className="mock-chart__title">Revenue <b>$247k <small>+12%</small></b></div>
                  <div className="mock-chart__bars" aria-hidden="true">
                    <i style={{ height: '38%' }} /><i style={{ height: '54%' }} /><i style={{ height: '45%' }} /><i style={{ height: '68%' }} /><i style={{ height: '61%' }} /><i style={{ height: '86%' }} /><i style={{ height: '75%' }} />
                  </div>
                  <div className="mock-chart__axis"><span>Sep</span><span>Oct</span><span>Nov</span><span>Dec</span><span>Jan</span><span>Feb</span></div>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  )
}
