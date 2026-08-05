import type { CSSProperties } from 'react'
import { caseStudies } from '../data'
import { Reveal } from './ui'

export function CaseStudyRail() {
  return (
    <section id="case-studies" className="case-study-section" aria-labelledby="case-study-title">
      <div className="container">
        <Reveal className="case-study-heading">
          <h2 id="case-study-title">Trusted by 100k+ businesses</h2>
          <span aria-hidden="true">Scroll to explore <b>→</b></span>
        </Reveal>
      </div>
      <div className="case-study-track" role="list" tabIndex={0} aria-label="Arin customer case studies. Scroll horizontally to explore.">
        {caseStudies.map((study, index) => (
          <Reveal key={study.name} className="case-study-card" role="listitem" delay={index * 45}>
            <article>
              <div className="case-study-card__image-wrap">
                <img src={study.image} alt={study.imageAlt} loading={index < 2 ? 'eager' : 'lazy'} />
                <span className="case-study-card__badge" style={{ '--badge-accent': study.accent } as CSSProperties}>
                  <span aria-hidden="true">✦</span>
                  {study.category}
                </span>
              </div>
              <div className="case-study-card__body">
                <strong>{study.name}</strong>
                <span><b>{study.metric}</b> {study.result}</span>
              </div>
            </article>
          </Reveal>
        ))}
      </div>
    </section>
  )
}
