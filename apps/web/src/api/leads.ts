export interface LeadPayload {
  product: string
  firstName: string
  lastName: string
  email: string
  phone: string
  thread_id?: string
}

export interface LeadRecord extends LeadPayload {
  timestamp: string
  thread_id: string
}

const POST_LEAD_API_URL = import.meta.env.VITE_POST_LEAD_API_URL || '/api/post-lead'
const GET_LEADS_API_URL = import.meta.env.VITE_GET_LEADS_API_URL || '/api/get-leads'

export async function submitLead(payload: LeadPayload): Promise<LeadRecord> {
  const res = await fetch(POST_LEAD_API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Lead API error (${res.status}): ${text}`)
  }

  const data = await res.json()
  return data.lead as LeadRecord
}

export async function fetchLeads(): Promise<LeadRecord[]> {
  const res = await fetch(GET_LEADS_API_URL)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Lead API error (${res.status}): ${text}`)
  }

  const data = await res.json()
  return (data.leads || []) as LeadRecord[]
}
