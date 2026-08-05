import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from 'react'

type PillProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  active?: boolean
  children: ReactNode
}

export function Pill({ active = false, className = '', children, ...props }: PillProps) {
  return (
    <button className={`pill ${active ? 'pill--active' : ''} ${className}`.trim()} {...props} aria-pressed={active}>
      {children}
    </button>
  )
}

type PrimaryButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  variant?: 'primary' | 'soft' | 'ghost'
}

export function PrimaryButton({ variant = 'primary', className = '', children, ...props }: PrimaryButtonProps) {
  return (
    <button className={`button button--${variant} ${className}`.trim()} {...props}>
      {children}
    </button>
  )
}

type SectionHeadingProps = {
  eyebrow?: string
  title: ReactNode
  description?: ReactNode
  align?: 'left' | 'center'
}

export function SectionHeading({ eyebrow, title, description, align = 'center' }: SectionHeadingProps) {
  return (
    <div className={`section-heading section-heading--${align}`}>
      {eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2>{title}</h2>
      {description && <p className="section-heading__description">{description}</p>}
    </div>
  )
}

type RevealProps = {
  children: ReactNode
  className?: string
  delay?: number
  role?: 'listitem'
}

export function Reveal({ children, className = '', delay = 0, role }: RevealProps) {
  return (
    <div className={`reveal ${className}`.trim()} role={role} style={{ '--reveal-delay': `${delay}ms` } as CSSProperties}>
      {children}
    </div>
  )
}
