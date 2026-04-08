/**
 * Reads src/generated/aimdk-manifest.json and writes src/content/developer-sidebar.json
 * with keys `en` and `zh`, optional basePath per locale, and grouped sections.
 */
import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '../..')
const MANIFEST = path.join(ROOT, 'src/generated/aimdk-manifest.json')
const OUT = path.join(ROOT, 'src/content/developer-sidebar.json')

function sectionKey(entry) {
  if (entry.product === 'aimdk') return 'hub'
  if (entry.product === 'downloads') return 'downloads'
  if (entry.product === 'a2w') return 'a2w'
  if (entry.product === 'a2-lite') return 'a2-lite'
  if (entry.product === 'a2') {
    return entry.section === 'motion' ? 'a2-motion' : 'a2-dev-guide'
  }
  return 'other'
}

function sectionTitle(key, locale) {
  const zh = locale === 'zh'
  switch (key) {
    case 'hub':
      return zh ? '概览' : 'Overview'
    case 'downloads':
      return zh ? '下载' : 'Downloads'
    case 'a2-dev-guide':
      return zh ? 'A2 开发指南' : 'A2 developer guide'
    case 'a2-motion':
      return zh ? 'A2 运控' : 'A2 motion'
    case 'a2w':
      return 'A2W'
    case 'a2-lite':
      return 'A2-lite'
    default:
      return 'Other'
  }
}

function sectionOrder(key) {
  const order = ['hub', 'downloads', 'a2-dev-guide', 'a2-motion', 'a2w', 'a2-lite', 'other']
  return order.indexOf(key)
}

async function main() {
  const raw = await fs.readFile(MANIFEST, 'utf8')
  const { entries } = JSON.parse(raw)

  function buildLocale(locale) {
    const prefix = `/developer/${locale}`
    const filtered = entries
      .filter((e) => e.eaiRoute === prefix || e.eaiRoute.startsWith(`${prefix}/`))
      .sort((a, b) => a.order - b.order || a.eaiRoute.localeCompare(b.eaiRoute))

    const bySection = new Map()
    for (const e of filtered) {
      const key = sectionKey(e)
      if (!bySection.has(key)) bySection.set(key, [])
      bySection.get(key).push(e)
    }

    const keys = [...bySection.keys()].sort((a, b) => sectionOrder(a) - sectionOrder(b))

    const sections = keys.map((key) => ({
      id: `developer-${locale}-${key}`,
      title: sectionTitle(key, locale),
      pages: bySection.get(key).map((e) => ({
        title: e.navTitle || e.title,
        slug: e.eaiRoute,
        file: path.posix.join('aimdk/content', e.contentFile),
      })),
    }))

    return {
      title: locale === 'zh' ? '开发者文档（中文）' : 'Developer documentation (English)',
      basePath: prefix,
      sections,
    }
  }

  const out = {
    en: buildLocale('en'),
    zh: buildLocale('zh'),
  }

  await fs.writeFile(OUT, `${JSON.stringify(out, null, 2)}\n`, 'utf8')
  console.log(`Wrote ${OUT}`)
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
