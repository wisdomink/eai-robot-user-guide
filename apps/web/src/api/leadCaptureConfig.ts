export interface LeadCaptureCopy {
  title_cn: string
  title_en: string
  description_cn: string
  description_en: string
  success_title_cn: string
  success_title_en: string
  success_text_cn: string
  success_text_en: string
  trigger_conditions_cn: string
  trigger_conditions_en: string
  [key: string]: string | undefined
}

export interface PurchaseIntentKeywords {
  cn: string[]
  en: string[]
}

export interface LeadCaptureTriageConfig {
  lead_capture: LeadCaptureCopy & Record<string, string | undefined>
  purchase_intent_keywords: PurchaseIntentKeywords
}

const GET_URL =
  import.meta.env.VITE_GET_LEAD_CAPTURE_CONFIG_API_URL || '/api/get-lead-capture-config'
const SAVE_URL =
  import.meta.env.VITE_SAVE_LEAD_CAPTURE_CONFIG_API_URL || '/api/save-lead-capture-config'

export async function fetchLeadCaptureTriageConfig(): Promise<LeadCaptureTriageConfig> {
  const res = await fetch(GET_URL)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Lead capture config API error (${res.status}): ${text}`)
  }
  return res.json() as Promise<LeadCaptureTriageConfig>
}

export async function saveLeadCaptureTriageConfig(
  payload: Partial<{
    lead_capture: Record<string, string>
    purchase_intent_keywords: PurchaseIntentKeywords
  }>
): Promise<LeadCaptureTriageConfig> {
  const res = await fetch(SAVE_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Lead capture config API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return data.config as LeadCaptureTriageConfig
}
