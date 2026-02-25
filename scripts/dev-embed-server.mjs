/**
 * Local development server for the embedding proxy.
 * Wraps the Lambda handler as a plain HTTP server.
 *
 * Usage:
 *   OPENAI_API_KEY=sk-... node scripts/dev-embed-server.mjs
 *
 * Listens on port 3001 by default (configurable via PORT env var).
 * Vite proxy forwards /api/embed → http://localhost:3001/api/embed
 */

import http from 'node:http'
import { handler } from '../lambda/embedding-proxy/index.mjs'

const PORT = process.env.PORT || 3001

const server = http.createServer(async (req, res) => {
  // Only handle POST /api/embed
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    })
    res.end()
    return
  }

  if (req.method !== 'POST' || req.url !== '/api/embed') {
    res.writeHead(404, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ error: 'Not found' }))
    return
  }

  // Read request body
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  const body = Buffer.concat(chunks).toString()

  // Build Lambda-style event
  const event = {
    body,
    httpMethod: 'POST',
    requestContext: {
      http: { method: 'POST', sourceIp: '127.0.0.1' },
    },
  }

  // Call the Lambda handler
  const result = await handler(event)

  // Send response
  res.writeHead(result.statusCode, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    ...result.headers,
  })
  res.end(result.body)
})

server.listen(PORT, () => {
  console.log(`\n  Embedding proxy running at http://localhost:${PORT}/api/embed\n`)
  if (!process.env.OPENAI_API_KEY) {
    console.log('  ⚠  OPENAI_API_KEY not set — requests will fail.\n')
  }
})
