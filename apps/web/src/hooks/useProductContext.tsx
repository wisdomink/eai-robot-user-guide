import allSidebars from '@/content/sidebar.json'

export type ProductId = keyof typeof allSidebars

const masterSidebar = allSidebars['master']

export interface ProductDef {
  id: ProductId
  label: string
  homeRoute: string
  homeFile: string
  sidebar: typeof masterSidebar
}

const PRODUCTS = Object.fromEntries(
  Object.entries(allSidebars).map(([id, sidebar]) => {
    const home = sidebar.sections[0]?.pages[0]
    if (!home) throw new Error(`Product "${id}" must define a home page as its first sidebar page.`)
    return [id, {
      id: id as ProductId,
      label: sidebar.title,
      homeRoute: home.slug,
      homeFile: home.file,
      sidebar,
    }]
  }),
) as Record<ProductId, ProductDef>

export const ALL_PRODUCTS = Object.values(PRODUCTS)
export const DOWNLOADABLE_PRODUCT_IDS: ProductId[] = [
  'futurist',
  'futurist-ultra',
  'master',
  'aegis',
  'aegis-ultra',
  'aegis-max',
  'navi',
]

export const DOWNLOADABLE_PRODUCTS = DOWNLOADABLE_PRODUCT_IDS.map(id => ({
  id,
  label: PRODUCTS[id].label,
}))
