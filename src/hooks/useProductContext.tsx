import allSidebars from '@/content/sidebar.json'

export type ProductId = 'master-ultra' | 'futurist-ultra' | 'aegis-edu' | 'aegis-ultra' | 'ff91'

const masterSidebar = allSidebars['master-ultra']

export interface ProductDef {
  id: ProductId
  label: string
  homeRoute: string
  homeFile: string
  sidebar: typeof masterSidebar
}

const PRODUCTS: Record<ProductId, ProductDef> = {
  'master-ultra': {
    id: 'master-ultra',
    label: 'Master',
    homeRoute: '/master-ultra',
    homeFile: 'master-ultra/master-ultra-home.md',
    sidebar: allSidebars['master-ultra'],
  },
  'futurist-ultra': {
    id: 'futurist-ultra',
    label: 'Futurist',
    homeRoute: '/futurist-ultra',
    homeFile: 'futurist-ultra/futurist-ultra-home.md',
    sidebar: allSidebars['futurist-ultra'],
  },
  'aegis-edu': {
    id: 'aegis-edu',
    label: 'Aegis EDU',
    homeRoute: '/aegis-edu',
    homeFile: 'aegis-edu/aegis-edu-home.md',
    sidebar: allSidebars['aegis-edu'],
  },
  'aegis-ultra': {
    id: 'aegis-ultra',
    label: 'Aegis',
    homeRoute: '/aegis-ultra',
    homeFile: 'aegis-ultra/aegis-ultra-home.md',
    sidebar: allSidebars['aegis-ultra'],
  },
  'ff91': {
    id: 'ff91',
    label: 'FF 91',
    homeRoute: '/ff91',
    homeFile: 'ff91/ff91-home.md',
    sidebar: allSidebars['ff91'],
  },
}

export const ALL_PRODUCTS = Object.values(PRODUCTS)
