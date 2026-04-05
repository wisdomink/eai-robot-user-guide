import allSidebars from '@/content/sidebar.json'

export type ProductId = 'futurist' | 'futurist-ultra' | 'master' | 'aegis' | 'aegis-ultra' | 'ff91'

const masterSidebar = allSidebars['master']

export interface ProductDef {
  id: ProductId
  label: string
  homeRoute: string
  homeFile: string
  sidebar: typeof masterSidebar
}

const PRODUCTS: Record<ProductId, ProductDef> = {
  'futurist': {
    id: 'futurist',
    label: 'FF Futurist',
    homeRoute: '/futurist',
    homeFile: 'futurist/futurist-home.md',
    sidebar: allSidebars['futurist'],
  },
  'futurist-ultra': {
    id: 'futurist-ultra',
    label: 'FF Futurist Ultra',
    homeRoute: '/futurist-ultra',
    homeFile: 'futurist-ultra/futurist-ultra-home.md',
    sidebar: allSidebars['futurist-ultra'],
  },
  'master': {
    id: 'master',
    label: 'FF Master',
    homeRoute: '/master',
    homeFile: 'master/master-home.md',
    sidebar: allSidebars['master'],
  },
  'aegis': {
    id: 'aegis',
    label: 'FF Aegis',
    homeRoute: '/aegis',
    homeFile: 'aegis/aegis-home.md',
    sidebar: allSidebars['aegis'],
  },
  'aegis-ultra': {
    id: 'aegis-ultra',
    label: 'FF Aegis Ultra',
    homeRoute: '/aegis-ultra',
    homeFile: 'aegis-ultra/aegis-ultra-home.md',
    sidebar: allSidebars['aegis-ultra'],
  },
  'ff91': {
    id: 'ff91',
    label: 'FF 91 2.0',
    homeRoute: '/ff91',
    homeFile: 'ff91/ff91-home.md',
    sidebar: allSidebars['ff91'],
  },
}

export const ALL_PRODUCTS = Object.values(PRODUCTS)
