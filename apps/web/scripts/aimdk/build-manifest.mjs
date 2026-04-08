/**
 * Scans src/content/aimdk/content for .mdx files, validates frontmatter, writes
 * src/generated/aimdk-manifest.json with eaiRoute = /developer + robotics route.
 */
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import matter from 'gray-matter'
import { z } from 'zod'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '../..')
const CONTENT_ROOT = path.join(ROOT, 'src/content/aimdk/content')
const OUT_FILE = path.join(ROOT, 'src/generated/aimdk-manifest.json')

const DOCS_PREFIX = '/developer'

const slugSegment = z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/i)

function isAppLocale(s) {
  return s === 'en' || s === 'zh'
}

const docFrontmatterSchema = z.object({
  title: z.string().min(1),
  description: z.string().optional(),
  product: z.string().optional(),
  version: z.string().optional(),
  section: z.string().optional(),
  slug: z.array(slugSegment).default([]),
  route: z
    .string()
    .regex(/^\//)
    .refine((r) => {
      const first = r.replace(/^\/+|\/+$/g, '').split('/').filter(Boolean)[0]
      return first && isAppLocale(first)
    }, 'route must start with /en or /zh'),
  sourceUrl: z.string().url().optional(),
  order: z.number().int().default(100),
  lastUpdated: z.string().optional(),
  navTitle: z.string().optional(),
  hideToc: z.boolean().optional(),
  hidePager: z.boolean().optional(),
})

const RESERVED_ROUTES = new Set(['/en', '/zh', '/en/downloads', '/zh/downloads'])

function routeToSlugSegments(route) {
  if (route === '/') return []
  const trimmed = route.replace(/^\/+|\/+$/g, '')
  if (!trimmed) return []
  return trimmed.split('/').filter(Boolean)
}

const NON_ALPHANUM = /[^a-z0-9]+/gi
function slugify(text) {
  return text
    .trim()
    .toLowerCase()
    .replace(NON_ALPHANUM, '-')
    .replace(/^-+|-+$/g, '')
}

function stripMarkdownForExcerpt(md, maxLen = 220) {
  const noCode = md.replace(/```[\s\S]*?```/g, ' ')
  const noInline = noCode.replace(/`[^`]+`/g, ' ')
  const plain = noInline
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[#>*_\-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  return plain.length > maxLen ? `${plain.slice(0, maxLen)}…` : plain
}

function extractHeadings(md) {
  const lines = md.split('\n')
  const out = []
  const used = new Map()
  for (const line of lines) {
    const m = /^(#{1,6})\s+(.+)$/.exec(line.trim())
    if (!m) continue
    const depth = m[1].length
    const text = m[2].replace(/\s+#+\s*$/, '').trim()
    let id = slugify(text)
    const n = used.get(id) ?? 0
    used.set(id, n + 1)
    if (n > 0) id = `${id}-${n}`
    out.push({ id, text, depth })
  }
  return out
}

async function walkMdx(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true })
  const files = []
  for (const e of entries) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) {
      if (e.name.startsWith('.') || e.name === '_import_staging') continue
      files.push(...(await walkMdx(p)))
    } else if (e.name.endsWith('.mdx')) {
      files.push(p)
    }
  }
  return files
}

async function main() {
  const mdxFiles = await walkMdx(CONTENT_ROOT)
  const entries = []

  for (const abs of mdxFiles) {
    const relPosix = path.relative(CONTENT_ROOT, abs).split(path.sep).join('/')
    const raw = await fs.readFile(abs, 'utf8')
    const { data, content: body } = matter(raw)

    let frontmatter
    try {
      frontmatter = docFrontmatterSchema.parse(data)
    } catch (err) {
      throw new Error(`Invalid frontmatter in ${relPosix}: ${err}`)
    }

    const slugSegments = routeToSlugSegments(frontmatter.route)
    if (!RESERVED_ROUTES.has(frontmatter.route) && slugSegments.length === 0) {
      throw new Error(`Non-reserved route must have slug segments: ${relPosix} route=${frontmatter.route}`)
    }

    const eaiRoute = `${DOCS_PREFIX}${frontmatter.route}`

    entries.push({
      ...frontmatter,
      contentFile: relPosix,
      slugSegments,
      eaiRoute,
      excerpt: stripMarkdownForExcerpt(body),
      headings: extractHeadings(body),
    })
  }

  const routes = new Set(entries.map((e) => e.route))
  if (routes.size !== entries.length) {
    const dup = entries.map((e) => e.route).filter((r, i, a) => a.indexOf(r) !== i)
    throw new Error(`Duplicate routes in manifest: ${[...new Set(dup)].join(', ')}`)
  }

  const eaiRoutes = new Set(entries.map((e) => e.eaiRoute))
  if (eaiRoutes.size !== entries.length) {
    throw new Error('Duplicate eaiRoute in manifest')
  }

  const manifest = {
    generatedAt: new Date().toISOString(),
    entries: entries.sort((a, b) => a.eaiRoute.localeCompare(b.eaiRoute)),
  }

  await fs.mkdir(path.dirname(OUT_FILE), { recursive: true })
  await fs.writeFile(OUT_FILE, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8')
  console.log(`Wrote ${entries.length} entries to ${path.relative(ROOT, OUT_FILE)}`)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
