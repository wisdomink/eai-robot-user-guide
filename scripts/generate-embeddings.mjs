/**
 * Build-time script: generates vector embeddings for all content chunks
 * using the OpenAI Embedding API (text-embedding-3-small).
 *
 * Usage:
 *   OPENAI_API_KEY=sk-... node scripts/generate-embeddings.mjs
 *
 * Output:
 *   public/search/embeddings.json
 */

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')

// ── Configuration ──────────────────────────────────────────────

const OPENAI_API_KEY = process.env.OPENAI_API_KEY
if (!OPENAI_API_KEY) {
  console.error('Error: OPENAI_API_KEY environment variable is required.')
  console.error('Usage: OPENAI_API_KEY=sk-... node scripts/generate-embeddings.mjs')
  process.exit(1)
}

const MODEL = 'text-embedding-3-small'
const DIMENSIONS = 512
const OUTPUT_PATH = path.resolve(root, 'public/search/embeddings.json')

// ── Load content ───────────────────────────────────────────────

const sidebar = JSON.parse(
  fs.readFileSync(path.resolve(root, 'src/content/sidebar.json'), 'utf-8')
)

function stripMarkdown(raw) {
  return raw
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/!\[[^\]]*\]\([^)]+\)/g, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[>|!\-]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
}

function toAnchor(heading) {
  return heading
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/^-|-$/g, '')
}

// Chunk all markdown content at ## headings
function buildChunks() {
  const chunks = []

  for (const section of sidebar.sections) {
    for (const page of section.pages) {
      const filePath = path.resolve(root, 'src/content/pages', page.file)
      if (!fs.existsSync(filePath)) {
        console.warn(`  ⚠ Missing file: ${page.file}`)
        continue
      }
      const raw = fs.readFileSync(filePath, 'utf-8')
      const parts = raw.split(/^(?=## )/m)

      for (const part of parts) {
        const headingMatch = part.match(/^## (.+)$/m)
        const sectionTitle = headingMatch ? headingMatch[1].trim() : page.title
        const anchor = headingMatch ? toAnchor(headingMatch[1].trim()) : ''
        const text = stripMarkdown(part)

        if (text.length < 20) continue

        chunks.push({
          id: `${page.file}#${anchor || 'top'}`,
          pageSlug: page.slug,
          pageTitle: page.title,
          sectionTitle,
          sectionId: section.id,
          headingAnchor: anchor,
          textPreview: text.slice(0, 200),
          text, // used for embedding, stripped before output
        })
      }
    }
  }

  return chunks
}

// ── Call OpenAI Embedding API ──────────────────────────────────

async function getEmbeddings(texts) {
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: MODEL,
      dimensions: DIMENSIONS,
      input: texts,
    }),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`OpenAI API error (${response.status}): ${error}`)
  }

  const data = await response.json()
  // Sort by index to ensure order matches input
  return data.data.sort((a, b) => a.index - b.index).map(d => d.embedding)
}

// ── Main ───────────────────────────────────────────────────────

async function main() {
  console.log('Generating embeddings for semantic search...\n')

  const chunks = buildChunks()
  console.log(`  Found ${chunks.length} content chunks across ${sidebar.sections.flatMap(s => s.pages).length} pages.\n`)

  // Batch embed all chunks (OpenAI supports up to 2048 inputs per request)
  const texts = chunks.map(c => c.text)
  console.log(`  Calling OpenAI ${MODEL} (dimensions=${DIMENSIONS})...`)
  const embeddings = await getEmbeddings(texts)
  console.log(`  ✓ Received ${embeddings.length} embeddings.\n`)

  // Build output (exclude full text, keep only preview)
  const output = {
    model: MODEL,
    dimensions: DIMENSIONS,
    generatedAt: new Date().toISOString(),
    chunks: chunks.map((chunk, i) => ({
      id: chunk.id,
      pageSlug: chunk.pageSlug,
      pageTitle: chunk.pageTitle,
      sectionTitle: chunk.sectionTitle,
      sectionId: chunk.sectionId,
      headingAnchor: chunk.headingAnchor,
      textPreview: chunk.textPreview,
      embedding: embeddings[i],
    })),
  }

  // Write output
  fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true })
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(output))

  const sizeKB = (Buffer.byteLength(JSON.stringify(output)) / 1024).toFixed(1)
  console.log(`  ✓ Written to ${path.relative(root, OUTPUT_PATH)} (${sizeKB} KB)`)
  console.log(`\nDone! ${chunks.length} chunks embedded.`)
}

main().catch(err => {
  console.error('Failed to generate embeddings:', err.message)
  process.exit(1)
})
