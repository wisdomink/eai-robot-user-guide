import { DOWNLOADABLE_PRODUCTS, type ProductId } from '@/hooks/useProductContext'

export const DEFAULT_MANUAL_DOWNLOAD_URLS: Record<ProductId, string> = {
  futurist: 'https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FF+Futurist.pdf',
  'futurist-ultra': 'https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FF+Futurist+Ultra.pdf',
  master: 'https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FF+Master.pdf',
  aegis: 'https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FX+Aegis.pdf',
  'aegis-ultra': 'https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FF+Aegis+Ultra.pdf',
  ff91: '',
  navi: 'https://ff-genesis-cdn-dev.s3.us-west-2.amazonaws.com/evan-test/download/FF+NAVI.pdf',
}

export interface ManualDownloadItem {
  product_id: ProductId
  label: string
  download_url: string
}

export interface ManualDownloadConfig {
  manual_downloads: ManualDownloadItem[]
}

const GET_URL =
  import.meta.env.VITE_GET_MANUAL_DOWNLOAD_CONFIG_API_URL || '/api/get-manual-download-config'
const SAVE_URL =
  import.meta.env.VITE_SAVE_MANUAL_DOWNLOAD_CONFIG_API_URL || '/api/save-manual-download-config'

export function getDefaultManualDownloadItems(): ManualDownloadItem[] {
  return DOWNLOADABLE_PRODUCTS.map(product => ({
    product_id: product.id,
    label: product.label,
    download_url: DEFAULT_MANUAL_DOWNLOAD_URLS[product.id],
  }))
}

function normalizeManualDownloads(raw: unknown): ManualDownloadItem[] {
  const rows = Array.isArray(raw) ? raw : []
  const byId = new Map(
    rows
      .filter((item): item is Partial<ManualDownloadItem> & { product_id: ProductId } => {
        if (!item || typeof item !== 'object') return false
        const productId = (item as { product_id?: unknown }).product_id
        return typeof productId === 'string'
      })
      .map(item => [item.product_id, item])
  )

  return DOWNLOADABLE_PRODUCTS.map(product => {
    const existing = byId.get(product.id)
    return {
      product_id: product.id,
      label: product.label,
      download_url:
        typeof existing?.download_url === 'string' && existing.download_url.trim()
          ? existing.download_url.trim()
          : DEFAULT_MANUAL_DOWNLOAD_URLS[product.id],
    }
  })
}

export async function fetchManualDownloadConfig(): Promise<ManualDownloadConfig> {
  const res = await fetch(GET_URL)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Manual download config API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return {
    manual_downloads: normalizeManualDownloads(data.manual_downloads),
  }
}

export async function saveManualDownloadConfig(
  payload: ManualDownloadConfig,
): Promise<ManualDownloadConfig> {
  const res = await fetch(SAVE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Manual download config API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return {
    manual_downloads: normalizeManualDownloads(data.config?.manual_downloads),
  }
}
