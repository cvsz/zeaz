import { testimonials } from '../data'
import { Reveal, SectionHeading } from './ui'

export function Testimonials() {
  return (
    <section id="testimonials" className="section testimonials-section" aria-labelledby="testimonials-title">
      <div className="container">
        <SectionHeading
          eyebrow="NEVER CODED BEFORE? NEITHER HAVE OUR CUSTOMERS"
          title={<span id="testimonials-title">Loved by <em className="gradient-text">100k+ businesses</em></span>}
          description="Small teams, ambitious founders, and growing businesses use Arin to turn ideas into software."
        />
        <div className="testimonial-grid">
          {testimonials.map((testimonial, index) => (
            <Reveal key={testimonial.name} className="testimonial-card" delay={index * 55}>
              <div className="testimonial-card__mark" aria-hidden="true">“</div>
              <p>{testimonial.quote}</p>
              <div className="testimonial-card__person">
                <span className={`avatar avatar--${testimonial.tone}`}>{testimonial.initials}</span>
                <span><strong>{testimonial.name}</strong><small>{testimonial.role}</small></span>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  )
}
