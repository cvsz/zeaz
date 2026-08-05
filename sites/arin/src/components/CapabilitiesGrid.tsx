import { capabilityGroups } from '../data'
import { Reveal, SectionHeading } from './ui'

export function CapabilitiesGrid() {
  return (
    <section id="capabilities" className="section capabilities-section" aria-labelledby="capabilities-title">
      <div className="container">
        <SectionHeading
          eyebrow="BUILT FOR THE WAY YOU WORK"
          title={<span id="capabilities-title">Everything you need <em className="gradient-text">is built-in</em></span>}
          description="Auth, hosting, backend, database, payments, email, API integrations, and 100s of other features all available instantly."
        />

        <div className="capability-groups">
          {capabilityGroups.map((group, index) => (
            <Reveal key={group.label} className="capability-group" delay={index * 80}>
              <div className="capability-group__header">
                <span>{String(index + 1).padStart(2, '0')}</span>
                <strong>{group.label}</strong>
              </div>
              <div className="capability-group__items" role="group" aria-label={group.label}>
                {[...group.items, ...group.items].map((item, itemIndex) => (
                  <span key={`${item}-${itemIndex}`}>
                    <i aria-hidden="true">✦</i>
                    {item}
                  </span>
                ))}
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
