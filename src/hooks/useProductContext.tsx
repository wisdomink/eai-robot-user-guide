import { createContext, useContext, useMemo, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import masterSidebar from '@/content/sidebar-master-ultra.json'
import futuristSidebar from '@/content/sidebar-futurist-ultra.json'
import aegiseduSidebar from '@/content/sidebar-aegis-edu.json'
import aegisSidebar from '@/content/sidebar-aegis-ultra.json'

export type ProductId = 'master-ultra' | 'futurist-ultra' | 'aegis-edu' | 'aegis-ultra'

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
    homeFile: 'master-ultra/home.md',
    sidebar: masterSidebar,
  },
  'futurist-ultra': {
    id: 'futurist-ultra',
    label: 'Futurist',
    homeRoute: '/futurist-ultra',
    homeFile: 'futurist-ultra/home.md',
    sidebar: futuristSidebar,
  },
  'aegis-edu': {
    id: 'aegis-edu',
    label: 'Aegis EDU',
    homeRoute: '/aegis-edu',
    homeFile: 'aegis-edu/home.md',
    sidebar: aegiseduSidebar,
  },
  'aegis-ultra': {
    id: 'aegis-ultra',
    label: 'Aegis',
    homeRoute: '/aegis-ultra',
    homeFile: 'aegis-ultra/home.md',
    sidebar: aegisSidebar,
  },
}

export const ALL_PRODUCTS = Object.values(PRODUCTS)

interface ProductContextValue {
  current: ProductDef
  switchProduct: (id: ProductId) => void
}

const ProductContext = createContext<ProductContextValue | null>(null)

function detectProduct(pathname: string): ProductId {
  if (pathname.startsWith('/futurist-ultra')) return 'futurist-ultra'
  if (pathname.startsWith('/aegis-edu')) return 'aegis-edu'
  if (pathname.startsWith('/aegis-ultra')) return 'aegis-ultra'
  return 'master-ultra'
}

export function ProductProvider({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()

  const productId = detectProduct(location.pathname)
  const current = PRODUCTS[productId]

  const switchProduct = useCallback(
    (id: ProductId) => {
      if (id !== productId) {
        navigate(PRODUCTS[id].homeRoute)
      }
    },
    [productId, navigate],
  )

  const value = useMemo(
    () => ({ current, switchProduct }),
    [current, switchProduct],
  )

  return (
    <ProductContext.Provider value={value}>
      {children}
    </ProductContext.Provider>
  )
}

export function useProduct() {
  const ctx = useContext(ProductContext)
  if (!ctx) throw new Error('useProduct must be used within ProductProvider')
  return ctx
}
