export interface RecommendationPayload {
  enabled: boolean
  product_name: string
  trigger_scene: string
  recommendation_content_cn: string
  recommendation_content_en: string
}

export interface RecommendationRecord extends RecommendationPayload {
  id: string
}

const GET_RECOMMENDATIONS_API_URL =
  import.meta.env.VITE_GET_RECOMMENDATIONS_API_URL || '/api/get-recommendations'
const SAVE_RECOMMENDATION_API_URL =
  import.meta.env.VITE_SAVE_RECOMMENDATION_API_URL || '/api/save-recommendation'
const DELETE_RECOMMENDATION_API_URL =
  import.meta.env.VITE_DELETE_RECOMMENDATION_API_URL || '/api/delete-recommendation'

export async function fetchRecommendations(): Promise<RecommendationRecord[]> {
  const res = await fetch(GET_RECOMMENDATIONS_API_URL)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Recommendation API error (${res.status}): ${text}`)
  }

  const data = await res.json()
  return (data.recommendations || []) as RecommendationRecord[]
}

export async function saveRecommendation(
  payload: RecommendationPayload & { id?: string }
): Promise<{ recommendation: RecommendationRecord; created: boolean }> {
  const res = await fetch(SAVE_RECOMMENDATION_API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Recommendation API error (${res.status}): ${text}`)
  }

  const data = await res.json()
  return {
    recommendation: data.recommendation as RecommendationRecord,
    created: Boolean(data.created),
  }
}

export async function deleteRecommendation(id: string): Promise<RecommendationRecord> {
  const res = await fetch(`${DELETE_RECOMMENDATION_API_URL}/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Recommendation API error (${res.status}): ${text}`)
  }

  const data = await res.json()
  return data.recommendation as RecommendationRecord
}
