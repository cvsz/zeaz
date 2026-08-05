export type Category = {
  id: string
  label: string
  icon: string
  prompt: string
}

export type CaseStudy = {
  category: string
  name: string
  image: string
  imageAlt: string
  metric: string
  result: string
  accent: string
}

export type CapabilityGroup = {
  label: string
  items: string[]
}

export type Testimonial = {
  quote: string
  name: string
  role: string
  initials: string
  tone: string
}

export type FaqItem = {
  question: string
  answer: string
}

export const categories: Category[] = [
  {
    id: 'internal',
    label: 'Internal software',
    icon: '▦',
    prompt: 'Build a CRM for my 12-person sales team that tracks deals and follow-ups…',
  },
  {
    id: 'customer',
    label: 'Customer software',
    icon: '♧',
    prompt: 'Build a client portal where customers can see project progress and invoices…',
  },
  {
    id: 'marketing',
    label: 'Marketing & SEO',
    icon: '⚑',
    prompt: 'Build a high-converting website for my service business with SEO tools…',
  },
  {
    id: 'mobile',
    label: 'Mobile apps',
    icon: '▣',
    prompt: 'Build a mobile app for my field team to capture jobs, photos, and signatures…',
  },
]

export const examplePrompts = ['CRM', 'ERP', 'HR portal', 'Inventory tracker', 'Operations dashboard']

export const caseStudies: CaseStudy[] = [
  {
    category: 'Logistics & Transportation',
    name: 'Petony Transportes',
    image: '/assets/customers/petony-transportes-team.jpg',
    imageAlt: 'Petony Transportes team gathered outside their transport business',
    metric: '+20%',
    result: 'Revenue growth',
    accent: '#2f83d6',
  },
  {
    category: 'Beverage Wholesale',
    name: 'Gamatauri',
    image: '/assets/customers/gamatauri-thales.png',
    imageAlt: 'Gamatauri founder photographed beside beverage products',
    metric: '+$200k',
    result: 'Added revenue',
    accent: '#7b5847',
  },
  {
    category: 'Law firm',
    name: 'Helixon Law',
    image: '/assets/customers/helixon-law-will.jpg',
    imageAlt: 'Will Helixon of Helixon Law photographed in an office',
    metric: '+30%',
    result: 'Higher close rate',
    accent: '#b3a58d',
  },
  {
    category: 'Home Services',
    name: 'MMA Plumbing',
    image: '/assets/customers/mma-plumbing-founder.png',
    imageAlt: 'MMA Plumbing founder photographed beside a service vehicle',
    metric: '€250k',
    result: 'Saved on software',
    accent: '#31524c',
  },
  {
    category: 'Motorcycle Manufacturing',
    name: 'Havoc Motorcycles',
    image: '/assets/customers/havoc-motorcycles-bike.png',
    imageAlt: 'Havoc Motorcycles custom motorcycle in a workshop',
    metric: '3 days',
    result: 'To relaunch',
    accent: '#171717',
  },
  {
    category: 'Construction',
    name: 'Kingdom Construction',
    image: '/assets/customers/kingdom-texas-team.jpeg',
    imageAlt: 'Kingdom Construction team posing at a construction site',
    metric: '$30k',
    result: 'Saved per year',
    accent: '#be8a43',
  },
  {
    category: 'Food & Beverage',
    name: 'The Ice Cream Hut',
    image: '/assets/customers/the-ice-cream-hut-cone.jpg',
    imageAlt: 'The Ice Cream Hut soft-serve cone against a bright background',
    metric: '30x',
    result: 'Website traffic',
    accent: '#df9665',
  },
  {
    category: 'Music & Entertainment',
    name: 'Sold Out',
    image: '/assets/customers/soldout-entertainment-stage.png',
    imageAlt: 'Sold Out entertainment stage lit with colorful concert lights',
    metric: '30x faster',
    result: 'Song releases',
    accent: '#242125',
  },
]

export const capabilityGroups: CapabilityGroup[] = [
  {
    label: 'Core infrastructure',
    items: ['Auth', 'Users', 'Database', 'Backend', 'Payments', 'Email', 'Storage', 'Hosting', 'Domains'],
  },
  {
    label: 'Experience & AI',
    items: ['Files & media', 'CMS', 'Search', 'Branding', 'SEO', 'Mobile', 'Chat', 'Notifications', 'AI text generation'],
  },
  {
    label: 'Intelligence',
    items: ['AI image generation', 'AI speech generation', 'AI transcription', 'Chatbots', 'AI Gateway', 'Realtime', '1,000s of API integrations'],
  },
  {
    label: 'Governance',
    items: ['Roles & permissions', 'Security', 'Secrets', 'Analytics', 'Audits', 'Version control', 'Scheduled events', 'Recurring events'],
  },
]

export const testimonials: Testimonial[] = [
  {
    quote: 'Every agency quoted me at least €250,000 to build what I wanted. Arin let me build it myself in a few weeks, without writing a single line of code.',
    name: 'Rachid',
    role: 'Founder, MMA Plumbing',
    initials: 'R',
    tone: 'coral',
  },
  {
    quote: 'I have tried every AI app builder and Arin is the best by far. The built-in backend and database are incredible.',
    name: 'Charlie S.',
    role: 'Founder, Modern Goods',
    initials: 'C',
    tone: 'lavender',
  },
  {
    quote: 'It used to take me six hours to build a legal packet. With the app I built on Arin, I do it in about fifteen minutes.',
    name: 'Will Helixon',
    role: 'Founder, Helixon Law',
    initials: 'W',
    tone: 'sand',
  },
  {
    quote: 'I was running a 15-person team and a physical office. Now almost everything runs on AI agents I built on Arin in a month.',
    name: 'Muhammad',
    role: 'Founder, Universal Marketing',
    initials: 'M',
    tone: 'blue',
  },
  {
    quote: 'A generic website was going to cost me $50,000. I paid far less for Arin and got a much better result: everything in one place.',
    name: 'Ron Ramsey',
    role: 'Founder, The Ice Cream Hut',
    initials: 'R',
    tone: 'peach',
  },
  {
    quote: 'I know zero about code, but I built an Arin app that pulled my whole business into one place. Our revenue is up around 20%.',
    name: 'Pedro Amaral',
    role: 'Founder, Petony Transportes',
    initials: 'P',
    tone: 'mint',
  },
]

export const faqItems: FaqItem[] = [
  {
    question: 'What is Arin?',
    answer: 'Arin is an AI app builder for business. Describe the software you need in plain language and Arin turns the idea into a working, publishable product.',
  },
  {
    question: 'How does Arin work?',
    answer: 'Start with a conversation. Arin creates the data model, interface, workflows, permissions, and supporting services as you refine the idea together.',
  },
  {
    question: 'What can I build with Arin?',
    answer: 'CRMs, portals, operations dashboards, inventory tools, marketing sites, mobile workflows, internal tools, and custom business software.',
  },
  {
    question: 'What features are built into Arin?',
    answer: 'Authentication, database, backend, hosting, domains, payments, email, storage, AI capabilities, analytics, integrations, and governance controls are ready when you need them.',
  },
  {
    question: 'Do I need coding experience?',
    answer: 'No. You can describe the outcome you want in everyday language. Developers can still inspect and refine the result when they want more control.',
  },
  {
    question: 'Can I publish to my own domain?',
    answer: 'Yes. A finished app can be published to a custom domain and shared with the people who need it.',
  },
  {
    question: 'Can I build mobile apps?',
    answer: 'Yes. Arin can create responsive experiences and mobile-ready workflows from the same conversational starting point.',
  },
]
