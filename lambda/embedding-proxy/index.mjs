/**
 * AWS Lambda function: proxies embedding requests to OpenAI API.
 *
 * Environment variables:
 *   OPENAI_API_KEY   - OpenAI API key
 *   ALLOWED_ORIGIN   - CORS origin (e.g., "https://manual.example.com")
 *
 * API Gateway setup:
 *   POST /api/embed  →  this Lambda
 *   Body: { "query": "search text" }
 *   Response: { "embedding": [0.012, -0.034, ...] }
 */

const MODEL = 'text-embedding-3-small'
const DIMENSIONS = 512

// Simple in-memory rate limiting (per Lambda instance)
const rateLimit = new Map()
const RATE_LIMIT_MAX = 60      // requests per window
const RATE_LIMIT_WINDOW = 60000 // 1 minute

function checkRateLimit(ip) {
  const now = Date.now()
  const entry = rateLimit.get(ip)
  if (!entry || now - entry.windowStart > RATE_LIMIT_WINDOW) {
    rateLimit.set(ip, { windowStart: now, count: 1 })
    return true
  }
  entry.count++
  return entry.count <= RATE_LIMIT_MAX
}

function corsHeaders(origin) {
  const allowed = process.env.ALLOWED_ORIGIN || '*'
  return {
    'Access-Control-Allow-Origin': allowed,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  }
}

export async function handler(event) {
  const headers = corsHeaders()

  // Handle CORS preflight
  if (event.requestContext?.http?.method === 'OPTIONS' || event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers, body: '' }
  }

  // Rate limit check
  const ip = event.requestContext?.http?.sourceIp
    || event.requestContext?.identity?.sourceIp
    || 'unknown'
  if (!checkRateLimit(ip)) {
    return {
      statusCode: 429,
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Rate limit exceeded. Try again later.' }),
    }
  }

  // Parse request
  let body
  try {
    body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body
  } catch {
    return {
      statusCode: 400,
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Invalid JSON body' }),
    }
  }

  const { query } = body || {}
  if (!query || typeof query !== 'string' || query.length > 500) {
    return {
      statusCode: 400,
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Missing or invalid "query" (string, max 500 chars)' }),
    }
  }

  // Call OpenAI
  try {
    const response = await fetch('https://api.openai.com/v1/embeddings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: MODEL,
        dimensions: DIMENSIONS,
        input: query,
      }),
    })

    if (!response.ok) {
      const error = await response.text()
      console.error('OpenAI API error:', response.status, error)
      return {
        statusCode: 502,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          error: 'Embedding service error',
          // Include upstream details in non-production for debugging
          ...(process.env.NODE_ENV !== 'production' && { detail: `OpenAI ${response.status}: ${error}` }),
        }),
      }
    }

    const data = await response.json()
    const embedding = data.data[0].embedding

    return {
      statusCode: 200,
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ embedding }),
    }
  } catch (err) {
    console.error('Lambda error:', err)
    return {
      statusCode: 500,
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Internal server error' }),
    }
  }
}
