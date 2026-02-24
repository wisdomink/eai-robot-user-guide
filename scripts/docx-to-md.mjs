#!/usr/bin/env node
/**
 * docx-to-md.mjs
 *
 * Converts the source Word document (manual.docx) into per-section
 * Markdown files under src/content/pages/.
 *
 * Usage:
 *   node scripts/docx-to-md.mjs
 *
 * What it does:
 *   1. Reads src/content/source/manual.docx via mammoth
 *   2. Converts to Markdown
 *   3. Splits by heading anchors into individual section files
 *   4. Extracts embedded images to public/images/
 *   5. Cleans up mammoth's escaped markdown syntax
 */

import { promises as fs } from 'node:fs'
import path from 'node:path'
import mammoth from 'mammoth'

const ROOT = path.resolve(import.meta.dirname, '..')
const DOCX_PATH = path.join(ROOT, 'src/content/source/manual.docx')
const PAGES_DIR = path.join(ROOT, 'src/content/pages')
const IMAGES_DIR = path.join(ROOT, 'public/images/docx')

// Section definitions: heading_id → { file, title }
// This mapping controls which headings become separate pages.
const SECTIONS = [
  { headingId: 'heading_1', file: 'safety-instructions.md', title: 'Safety Instructions' },
  { headingId: 'heading_2', file: 'safety-guidelines.md', title: 'Safety Guidelines' },
  { headingId: 'heading_3', file: 'maintenance.md', title: 'Maintenance and Management Guidelines' },
  { headingId: 'heading_5', file: 'packing-list.md', title: 'Packing List' },
  { headingId: 'heading_6', file: 'product-overview.md', title: 'Product Overview' },
  { headingId: 'heading_7', file: 'product-structure.md', title: 'Product Structure Diagram' },
  { headingId: 'heading_8', file: 'debugging-interface.md', title: 'User Debugging Interface' },
  { headingId: 'heading_9', file: 'sdk-interface.md', title: 'Software Development Kit Interface' },
  { headingId: 'heading_10', file: 'computational-unit.md', title: 'Computational Unit' },
  { headingId: 'heading_11', file: 'battery-indicator.md', title: 'Battery Indicator Lights' },
]

/**
 * Clean up mammoth's markdown output:
 * - Remove excessive backslash escaping
 * - Convert __text__ to **text** (bold)
 * - Remove anchor tags
 * - Clean up heading syntax
 */
function cleanMarkdown(md) {
  let result = md
    // Remove anchor tags
    .replace(/<a id="[^"]*"><\/a>/g, '')
    // Convert __text__ to **text**
    .replace(/__([^_]+)__/g, '**$1**')
    // Remove backslash escapes from mammoth (including \- for hyphens)
    // Do this early so heading/number patterns are clean for later regexes
    .replace(/\\([.\-()[\]{}*+?^$|#!])/g, '$1')
    // Remove standalone chapter heading lines like "1.1 **Safety Instructions**"
    // These duplicate the h1 title we add manually
    .replace(/^\d+(?:\.\d+)*\s+\*\*[^*]+\*\*\s*$/gm, '')
    // Fix bold markers with trailing space: "**text: **" → "**text:**"
    // Mammoth preserves trailing spaces inside bold which breaks markdown rendering
    .replace(/\*\*([^*\n]+?)\s+\*\*/g, '**$1** ')
    // Clean up double spaces
    .replace(/  +/g, ' ')
    // Remove multiple consecutive blank lines
    .replace(/\n{3,}/g, '\n\n')
    // Remove leading/trailing blank lines
    .trim()

  return result
}

/**
 * Extract base64 images from markdown, save to disk, replace with file paths.
 */
async function extractImages(md, sectionFile) {
  await fs.mkdir(IMAGES_DIR, { recursive: true })

  let imageIndex = 0
  const sectionName = path.basename(sectionFile, '.md')

  const result = md.replace(
    /!\[([^\]]*)\]\(data:image\/([^;]+);base64,([^)]+)\)/g,
    (match, alt, ext, base64Data) => {
      imageIndex++
      const filename = `${sectionName}-${imageIndex}.${ext === 'x-emf' ? 'png' : ext}`
      const filepath = path.join(IMAGES_DIR, filename)

      // Write image file (sync-style via promise collection)
      const buffer = Buffer.from(base64Data, 'base64')
      fs.writeFile(filepath, buffer).catch(err => {
        console.warn(`  Warning: Failed to write image ${filename}:`, err.message)
      })

      return `![${alt}](/images/docx/${filename})`
    }
  )

  return result
}

async function main() {
  console.log('Reading:', DOCX_PATH)

  const docxBuffer = await fs.readFile(DOCX_PATH)
  const result = await mammoth.convertToMarkdown({ buffer: docxBuffer })

  if (result.messages.length > 0) {
    console.log('Warnings:', result.messages.length)
  }

  const fullMd = result.value
  console.log(`Converted: ${fullMd.length} characters of markdown`)

  // Find all heading positions
  const headingRegex = /<a id="(heading_\d+)"><\/a>/g
  const headings = []
  let m
  while ((m = headingRegex.exec(fullMd)) !== null) {
    headings.push({ id: m[1], pos: m.index })
  }

  console.log(`Found ${headings.length} headings`)

  // Create pages directory
  await fs.mkdir(PAGES_DIR, { recursive: true })

  // Extract each section
  for (const section of SECTIONS) {
    const headingIdx = headings.findIndex(h => h.id === section.headingId)
    if (headingIdx === -1) {
      console.warn(`  Heading ${section.headingId} not found, skipping ${section.file}`)
      continue
    }

    const startPos = headings[headingIdx].pos

    // Use the very next heading in document order as end boundary
    // This avoids capturing content from intermediate headings we skip
    let endPos = fullMd.length
    if (headingIdx + 1 < headings.length) {
      endPos = headings[headingIdx + 1].pos
    }

    let sectionMd = fullMd.substring(startPos, endPos)

    // Add title as h1
    sectionMd = `# ${section.title}\n\n${cleanMarkdown(sectionMd)}`

    // Extract images
    sectionMd = await extractImages(sectionMd, section.file)

    const outPath = path.join(PAGES_DIR, section.file)
    await fs.writeFile(outPath, sectionMd, 'utf-8')
    console.log(`  Written: ${section.file}`)
  }

  console.log('\nDone! Chapter files written to src/content/pages/')
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})
