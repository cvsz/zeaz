import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { categories, examplePrompts, type Category } from '../data'
import { Pill, PrimaryButton, Reveal } from './ui'
import { ApiError, api } from '../api'

type HeroBuilderProps = {
  activeCategory: string
  onCategoryChange: (id: string) => void
}

export function HeroBuilder({ activeCategory, onCategoryChange }: HeroBuilderProps) {
  const selectedCategory = categories.find((category) => category.id === activeCategory) ?? categories[0]
  const [prompt, setPrompt] = useState(selectedCategory.prompt)
  const [isBuilding, setIsBuilding] = useState(false)
  const [status, setStatus] = useState('')

  useEffect(() => {
    setPrompt(selectedCategory.prompt)
    setStatus('')
  }, [selectedCategory])

  function handleCategoryChange(category: Category) {
    onCategoryChange(category.id)
    setPrompt(category.prompt)
    setStatus('')
  }

  async function handleBuild(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (isBuilding) return
    setIsBuilding(true)
    setStatus('')
    try {
      await api.session()
      window.location.assign('/studio')
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        window.location.assign('/auth?mode=register&next=/studio')
      } else {
        setStatus('Open your workspace to start a real build.')
      }
    } finally {
      setIsBuilding(false)
    }
  }

  return (
    <section id="hero" className="hero" aria-labelledby="hero-title">
      <div className="container hero__inner">
        <Reveal className="hero__copy">
          <h1 id="hero-title">
            The Best <span>AI App Builder</span> for Business
          </h1>
          <p>Build custom software for your business without hiring a developer</p>
        </Reveal>

        <Reveal className="category-tabs" delay={80}>
          <div className="category-tabs__group" role="group" aria-label="Choose what to build">
          {categories.map((category) => (
            <Pill
              key={category.id}
              active={category.id === activeCategory}
              onClick={() => handleCategoryChange(category)}
              type="button"
            >
              <span className="pill__icon" aria-hidden="true">{category.icon}</span>
              {category.label}
            </Pill>
          ))}
          </div>
        </Reveal>

        <Reveal className="prompt-builder" delay={140}>
          <form className="prompt-card" onSubmit={handleBuild}>
            <label className="sr-only" htmlFor="app-prompt">Describe what you want to build</label>
            <textarea
              id="app-prompt"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder={selectedCategory.prompt}
              rows={3}
            />
            <div className="prompt-card__footer">
              <div className="prompt-tools">
                <button type="button" className="prompt-tool" aria-label="Attach an image">
                  <span aria-hidden="true">▧</span>
                  Attach Image
                </button>
                <button type="button" className="prompt-tool" aria-label="Choose build mode">
                  <span aria-hidden="true">⌁</span>
                  Build mode
                </button>
              </div>
              <PrimaryButton type="submit" disabled={isBuilding}>
                {isBuilding ? 'Building…' : 'Build it'}
                <span aria-hidden="true">→</span>
              </PrimaryButton>
            </div>
          </form>
          <p className="prompt-status" aria-live="polite">{status}</p>
        </Reveal>

        <Reveal className="example-prompts" delay={220}>
          <span>Try it <span aria-hidden="true">→</span></span>
          {examplePrompts.map((example) => (
            <button key={example} type="button" onClick={() => setPrompt(`Build a ${example} for my business…`)}>
              {example}
            </button>
          ))}
        </Reveal>

        <Reveal className="trust-line" delay={280}>
          <span className="trust-line__spark" aria-hidden="true">✦</span>
          Trusted by 100k+ businesses
        </Reveal>
      </div>
    </section>
  )
}
