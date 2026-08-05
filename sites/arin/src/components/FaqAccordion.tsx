import { faqItems } from '../data'

type FaqAccordionProps = {
  openIndex: number | null
  onToggle: (index: number) => void
}

export function FaqAccordion({ openIndex, onToggle }: FaqAccordionProps) {
  return (
    <section id="faq" className="section faq-section" aria-labelledby="faq-title">
      <div className="container faq-layout">
        <div className="faq-intro">
          <p className="eyebrow">QUESTIONS, ANSWERED</p>
          <h2 id="faq-title">Build with confidence.</h2>
          <p>Everything you need to go from a first idea to software your team can rely on.</p>
        </div>
        <div className="faq-list">
          {faqItems.map((item, index) => {
            const isOpen = openIndex === index
            const answerId = `faq-answer-${index}`
            return (
              <div className={`faq-item ${isOpen ? 'faq-item--open' : ''}`} key={item.question}>
                <button type="button" aria-expanded={isOpen} aria-controls={answerId} onClick={() => onToggle(index)}>
                  <span>{item.question}</span>
                  <span aria-hidden="true">{isOpen ? '−' : '+'}</span>
                </button>
                <div id={answerId} className="faq-answer" hidden={!isOpen}>
                  <p>{item.answer}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
