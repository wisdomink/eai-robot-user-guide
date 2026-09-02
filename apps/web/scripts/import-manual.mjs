#!/usr/bin/env node
/**
 * Import a DOCX manual into the static Markdown content structure.
 *
 * Usage:
 *   npm run manual:import -- --config scripts/manuals/aegis-max.json [--dry-run]
 */
import { promises as fs } from 'node:fs'
import path from 'node:path'
import mammoth from 'mammoth'

const WEB_ROOT = path.resolve(import.meta.dirname, '..')
const REPO_ROOT = path.resolve(WEB_ROOT, '../..')

function arg(name) {
  const index = process.argv.indexOf(name)
  return index === -1 ? undefined : process.argv[index + 1]
}

function decodeHtml(value) {
  return value
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
}

function textFromHtml(value, lineBreak = ' ') {
  return decodeHtml(value)
    .replace(/<br\s*\/?\s*>/gi, '\n')
    .replace(/<\/p>\s*<p>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/\s*\n\s*/g, lineBreak)
    .replace(/\s+/g, ' ')
    .trim()
}

function tableToMarkdown(tableHtml) {
  const rows = [...tableHtml.matchAll(/<tr>([\s\S]*?)<\/tr>/gi)].map(([, row]) =>
    [...row.matchAll(/<t[dh]>([\s\S]*?)<\/t[dh]>/gi)].map(([, cell]) =>
      textFromHtml(cell, '<br>').replaceAll('|', '\\|'),
    ),
  )
  if (!rows.length) return ''
  const width = Math.max(...rows.map(row => row.length))
  const normalised = rows.map(row => [...row, ...Array(width - row.length).fill('')])
  if (width === 1) return `> **Review note:** ${normalised.flat().filter(Boolean).join(' ')}`
  return [
    `| ${normalised[0].join(' | ')} |`,
    `| ${Array(width).fill('---').join(' | ')} |`,
    ...normalised.slice(1).map(row => `| ${row.join(' | ')} |`),
  ].join('\n')
}

function paragraphToMarkdown(html, config) {
  const image = html.match(/<img[^>]+src="([^"]+)"[^>]*>/i)
  if (image) {
    const number = Number(image[1].match(/-(\d+)\.[a-z0-9]+$/i)?.[1] ?? 0)
    const alt = config.images.altText?.[number] ?? `FF Aegis Max figure ${number} — description pending review`
    return `![${alt}](${image[1]})`
  }
  const text = textFromHtml(html)
  if (!text) return ''
  if (text.startsWith('Source figure')) return `*${text}*`
  if (/^\d+\.\d+\s+/.test(text)) return `## ${text}`
  if (/^[A-Z]\.\s+/.test(text)) return `### ${text}`
  if (config.subheadings.includes(text)) return `### ${text}`
  return text
}

function htmlToBlocks(html, config) {
  const tables = []
  const withoutTables = html.replace(/<table>[\s\S]*?<\/table>/gi, table => {
    tables.push(table)
    return `@@TABLE_${tables.length - 1}@@`
  })
  const blocks = []
  const pattern = /<p>[\s\S]*?<\/p>|<ul>[\s\S]*?<\/ul>|@@TABLE_\d+@@/gi
  for (const match of withoutTables.matchAll(pattern)) {
    const token = match[0]
    const table = token.match(/^@@TABLE_(\d+)@@$/)
    if (table) {
      blocks.push({ type: 'table', value: tableToMarkdown(tables[Number(table[1])]) })
    } else if (token.startsWith('<ul>')) {
      const items = [...token.matchAll(/<li>([\s\S]*?)<\/li>/gi)]
        .map(([, item]) => textFromHtml(item))
        .filter(Boolean)
        .map(item => `- ${item}`)
        .join('\n')
      blocks.push({ type: 'content', value: items })
    } else {
      blocks.push({ type: 'paragraph', value: paragraphToMarkdown(token, config), text: textFromHtml(token) })
    }
  }
  return blocks.filter(block => block.value)
}

function buildHome(config) {
  const checks = config.home.releaseChecks.map(check => `- ${check}`).join('\n')
  return `# ${config.title}\n\n*${config.home.subtitle}*\n\n> **Publication review required:** ${config.home.reviewNotice}\n\n## Items to resolve before external release\n\n${checks}\n\nSee the sidebar for the imported manual content.\n`
}

function buildPages(blocks, config) {
  const pages = new Map(config.chapters.map(chapter => [chapter.number, []]))
  let chapter
  for (const block of blocks) {
    if (block.type === 'paragraph') {
      const match = block.text.match(/^(\d+)\.\s+/)
      if (match && pages.has(Number(match[1]))) {
        chapter = Number(match[1])
        continue
      }
    }
    if (chapter) pages.get(chapter).push(block.value)
  }
  return config.chapters.map(chapter => ({
    file: chapter.file,
    content: applyReplacements(`# ${chapter.title}\n\n${pages.get(chapter.number).join('\n\n')}\n`, config.replacements),
  }))
}

function applyReplacements(content, replacements = []) {
  return replacements.reduce(
    (result, { from, to }) => result.replaceAll(from, to),
    content,
  )
}

async function writeIfChanged(file, content, dryRun) {
  let current = ''
  try { current = await fs.readFile(file, 'utf8') } catch { /* new file */ }
  if (current === content) return false
  if (!dryRun) {
    await fs.mkdir(path.dirname(file), { recursive: true })
    await fs.writeFile(file, content, 'utf8')
  }
  return true
}

function extensionFor(contentType) {
  if (contentType === 'image/jpeg') return 'jpg'
  if (contentType === 'image/svg+xml') return 'svg'
  return contentType.split('/')[1] ?? 'bin'
}

async function extractImages(sourcePath, config, dryRun) {
  const imageDir = path.resolve(WEB_ROOT, 'public/images', config.images.directory)
  const prefix = `${config.id}-figure-`
  const expected = new Set()
  let changed = 0
  let count = 0
  if (!dryRun) await fs.mkdir(imageDir, { recursive: true })

  const result = await mammoth.convertToHtml(
    { path: sourcePath },
    {
      convertImage: mammoth.images.imgElement(async image => {
        const number = ++count
        const filename = `${prefix}${String(number).padStart(2, '0')}.${extensionFor(image.contentType)}`
        const target = path.join(imageDir, filename)
        const buffer = await image.read()
        expected.add(filename)
        let current
        try { current = await fs.readFile(target) } catch { /* new image */ }
        if (!current || !current.equals(buffer)) {
          changed += 1
          if (!dryRun) await fs.writeFile(target, buffer)
        }
        return { src: `/images/${config.images.directory}/${filename}` }
      }),
    },
  )

  let existing = []
  try { existing = await fs.readdir(imageDir) } catch { /* directory is new */ }
  const stale = existing.filter(file => file.startsWith(prefix) && !expected.has(file))
  changed += stale.length
  if (!dryRun) await Promise.all(stale.map(file => fs.unlink(path.join(imageDir, file))))
  return { html: result.value, messages: result.messages, count, changed, stale }
}

async function main() {
  const configArg = arg('--config')
  if (!configArg) throw new Error('Missing --config. See scripts/manuals/aegis-max.json for an example.')
  const configPath = path.resolve(WEB_ROOT, configArg)
  const config = JSON.parse(await fs.readFile(configPath, 'utf8'))
  const sourcePath = path.resolve(REPO_ROOT, config.source)
  const outputDir = path.resolve(WEB_ROOT, 'src/content/pages', config.id)
  const dryRun = process.argv.includes('--dry-run')
  const imageResult = await extractImages(sourcePath, config, dryRun)
  if (imageResult.messages.length) console.warn(imageResult.messages)

  const blocks = htmlToBlocks(imageResult.html, config)
  const files = [{ file: 'home.md', content: buildHome(config) }, ...buildPages(blocks, config)]
  let changed = 0
  for (const page of files) {
    if (await writeIfChanged(path.join(outputDir, `${config.id}-${page.file}`), page.content, dryRun)) changed += 1
  }
  console.log(`${dryRun ? 'Would update' : 'Updated'} ${changed}/${files.length} Markdown files and ${imageResult.changed}/${imageResult.count} images for ${config.title}.`)
  if (imageResult.stale.length) console.log(`Removed ${imageResult.stale.length} stale image(s): ${imageResult.stale.join(', ')}`)
}

main().catch(error => {
  console.error(error.message)
  process.exit(1)
})
