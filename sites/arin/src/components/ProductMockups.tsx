import { SectionHeading } from './ui'

export function DashboardMockup() {
  return (
    <div className="dashboard-card">
      <div className="dashboard-card__topbar">
        <div className="window-dots" aria-hidden="true"><i /><i /><i /></div>
        <span>Dashboard</span>
        <span className="dashboard-card__publish">v1 <span aria-hidden="true">↗</span> Publish</span>
      </div>
      <div className="dashboard-card__content">
        <div className="dashboard-card__title"><span>Revenue overview</span><button type="button">Last 6 months⌄</button></div>
        <div className="dashboard-metric-row">
          <div><span>Active Deals</span><strong>128<small>+8%</small></strong></div>
          <div><span>Win Rate</span><strong>42%<small>+4%</small></strong></div>
          <div><span>Avg Deal</span><strong>$89k<small>+6%</small></strong></div>
          <div><span>Revenue</span><strong>$247k<small>+12%</small></strong></div>
        </div>
        <div className="dashboard-chart" role="img" aria-label="Revenue increased across the last six months">
          <div className="dashboard-chart__grid"><i /><i /><i /><i /></div>
          <svg viewBox="0 0 720 180" role="img" aria-hidden="true" preserveAspectRatio="none">
            <defs>
              <linearGradient id="chart-fill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0" stopColor="#4855f5" stopOpacity=".24" />
                <stop offset="1" stopColor="#4855f5" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path d="M0 154 C72 150 75 119 130 128 S205 92 254 111 S323 75 377 91 S440 51 500 70 S560 22 612 49 S671 34 720 16 V180 H0 Z" fill="url(#chart-fill)" />
            <path d="M0 154 C72 150 75 119 130 128 S205 92 254 111 S323 75 377 91 S440 51 500 70 S560 22 612 49 S671 34 720 16" fill="none" stroke="#4352ec" strokeLinecap="round" strokeWidth="4" />
          </svg>
          <div className="dashboard-chart__labels"><span>Sep</span><span>Oct</span><span>Nov</span><span>Dec</span><span>Jan</span><span>Feb</span></div>
        </div>
      </div>
    </div>
  )
}

export function ScalePanel() {
  return (
    <article className="scale-panel product-panel">
      <div className="panel-kicker"><span className="panel-icon panel-icon--blue" aria-hidden="true">↗</span><span>Scale to millions</span></div>
      <strong>750,000</strong>
      <span className="panel-caption">active users</span>
      <p>Arin apps are serverless, so they scale up to as much traffic as you need without breaking.</p>
      <div className="scale-lines" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /><i /></div>
    </article>
  )
}

export function GovernancePanel() {
  const users = [
    { initials: 'A', name: 'Alex Rivera', role: 'Admin', tone: 'blue' },
    { initials: 'S', name: 'Sam Chen', role: 'Viewer', tone: 'peach' },
    { initials: 'J', name: 'Jordan Lee', role: 'Viewer', tone: 'lavender' },
  ]

  return (
    <article className="governance-panel product-panel">
      <div className="panel-kicker"><span className="panel-icon panel-icon--green" aria-hidden="true">✓</span><span>Govern with confidence</span></div>
      <p className="governance-copy">Apps are secure and private, with best-in-class uptime and permission management.</p>
      <div className="governance-table">
        <div className="governance-table__heading"><span>Users &amp; Roles</span><button type="button">+ Invite</button></div>
        {users.map((user) => (
          <div className="governance-user" key={user.name}>
            <span className={`avatar avatar--${user.tone}`}>{user.initials}</span>
            <span>{user.name}</span>
            <small>{user.role}</small>
          </div>
        ))}
      </div>
    </article>
  )
}

export function ProductMockups() {
  return (
    <section id="scale" className="section product-section" aria-labelledby="publish-title">
      <div className="container">
        <SectionHeading
          eyebrow="PUBLISH IN A CLICK"
          title={<span id="publish-title">From idea to <em className="gradient-text">everywhere</em></span>}
          description="Deploy your app to a custom domain instantly. You can also publish to the iOS App Store or Google Play Store."
        />
        <DashboardMockup />
        <div className="product-panels">
          <ScalePanel />
          <GovernancePanel />
        </div>
      </div>
    </section>
  )
}
