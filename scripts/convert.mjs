#!/usr/bin/env node
/**
 * convert.mjs — Unified source-to-markdown conversion pipeline
 *
 * Hybrid approach: PDF for text extraction, Word for image extraction.
 * Both are merged into final markdown files with correctly placed images.
 *
 * Prerequisites:
 *   brew install poppler   (provides pdftotext)
 *   npm install             (provides mammoth)
 *
 * Usage:
 *   npm run convert               # full pipeline (text + images)
 *   npm run convert:text           # text only (no image extraction/insertion)
 *   npm run convert:images         # images only (extract from Word, no text regen)
 *
 * Source files:
 *   src/content/source/manual.pdf   — text source (pdftotext -layout)
 *   src/content/source/manual.docx  — image source (mammoth)
 *
 * Output:
 *   src/content/pages/*.md          — markdown files with image references
 *   public/images/docx/*            — extracted image files
 */

import { promises as fs } from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import mammoth from 'mammoth'

// ─── Paths ──────────────────────────────────────────────────────────────────

const ROOT = path.resolve(import.meta.dirname, '..')
const PDF_PATH = path.join(ROOT, 'src/content/source/manual.pdf')
const DOCX_PATH = path.join(ROOT, 'src/content/source/manual.docx')
const PAGES_DIR = path.join(ROOT, 'src/content/pages')
const IMAGES_DIR = path.join(ROOT, 'public/images/docx')

// ─── Section Definitions ────────────────────────────────────────────────────
//
// Each section is the single source of truth for:
//   - PDF text extraction: pattern, endBefore
//   - Word image extraction: headingId (per image rule)
//   - Image placement: images[] rules
//
// Image placement rules:
//   position: 'start'          → after the # title line
//   position: 'end'            → at the end of the file
//   after: '## Heading Text'   → right after that heading line
//   after: 'text fragment'     → after the first line containing this text
//
// Each image rule extracts from Word using its own headingId/endHeadingId,
// allowing one markdown file to pull images from multiple Word sections.

const SECTIONS = [
  // ── Chapter 1: Preliminary Notice ──────────────────────────────────────
  {
    chapter: 1,
    file: 'safety-instructions.md',
    title: 'Safety Instructions',
    pattern: /^1\.1\s+Safety Instructions\s*$/m,
    endBefore: /^1\.2\s/m,
  },
  {
    chapter: 1,
    file: 'safety-guidelines.md',
    title: 'Safety Guidelines',
    pattern: /^1\.2\s+Safety Guidelines\s*$/m,
    endBefore: /^1\.3\s/m,
  },
  {
    chapter: 1,
    file: 'maintenance.md',
    title: 'Maintenance and Management Guidelines',
    pattern: /^1\.3\s+Maintenance and Management Guidelines\s*$/m,
    endBefore: /^2\.\s{1,2}[A-Z]/m,
  },

  // ── Chapter 2: About FF Master ─────────────────────────────────────────
  {
    chapter: 2,
    file: 'packing-list.md',
    title: 'Packing List',
    pattern: /^2\.1\s+Packing List\s*$/m,
    endBefore: /^2\.2\s/m,
    images: [
      { position: 'start', headingId: 'heading_5', name: 'packing-list', alts: ['Package Contents'] },
    ],
  },
  {
    chapter: 2,
    file: 'product-overview.md',
    title: 'Product Overview',
    pattern: /^2\.2\s+Product Overview\s*$/m,
    endBefore: /^2\.3\s/m,
    images: [
      { after: '## Product Structure Diagram', headingId: 'heading_7', name: 'product-structure' },
      { after: '## User Debugging Interface', headingId: 'heading_8', name: 'debugging-interface' },
      { position: 'end', headingId: 'heading_9', name: 'sdk-interface' },
    ],
  },
  {
    chapter: 2,
    file: 'computational-unit.md',
    title: 'Computational Unit',
    pattern: /^2\.3\s+Computational Unit\s*$/m,
    endBefore: /^2\.4\s/m,
  },
  {
    chapter: 2,
    file: 'battery-indicator.md',
    title: 'Battery Indicator Lights',
    pattern: /^2\.4\s+Battery Indicator Lights\s*$/m,
    endBefore: /^2\.5\s/m,
    images: [
      { after: '## Battery Indicator Location', headingId: 'heading_11', endHeadingId: 'heading_17', name: 'battery-indicator' },
    ],
  },
  {
    chapter: 2,
    file: 'sensor-fov.md',
    title: 'Sensor Field of View',
    pattern: /^2\.5\s+Sensor Field of View\s*$/m,
    endBefore: /^2\.6\s/m,
    images: [
      {
        position: 'end', headingId: 'heading_17', name: 'sensor-fov',
        alts: ['Lidar-FOV', 'RGBD-FOV', 'Interactive RGB Camera-FOV-Vertical', 'Interactive RGB Camera-FOV-Horizontal'],
      },
    ],
  },
  {
    chapter: 2,
    file: 'joint-limits.md',
    title: 'Joint Name and Joint Limit',
    pattern: /^2\.6\s+Joint Name and Joint Limit\s*$/m,
    endBefore: /^2\.7\s/m,
    images: [
      { position: 'start', headingId: 'heading_18', name: 'joint-limits' },
    ],
  },
  {
    chapter: 2,
    file: 'coordinate-systems.md',
    title: 'Coordinate Systems',
    pattern: /^2\.7\s+Coordinate Systems\s*$/m,
    endBefore: /^2\.8\s/m,
    images: [
      { position: 'end', headingId: 'heading_19', name: 'coordinate-systems' },
    ],
  },
  {
    chapter: 2,
    file: 'specifications.md',
    title: 'Specifications',
    pattern: /^2\.8\s+Specifications\s*$/m,
    endBefore: /^3\.\s{1,2}[A-Z]/m,
  },
]

// ─── Step 1: Image Extraction (Word → images) ──────────────────────────────

/**
 * Extract images from Word document using mammoth.
 * @param {typeof SECTIONS} sections — filtered sections to process
 * Returns a map: imageName → [filename1, filename2, ...]
 */
async function extractImages(sections) {
  console.log('\n── Step 1: Extracting images from Word ──')
  console.log('Reading:', DOCX_PATH)

  const docxBuffer = await fs.readFile(DOCX_PATH)
  const result = await mammoth.convertToMarkdown({ buffer: docxBuffer })
  const fullMd = result.value

  // Find all heading positions
  const headingRegex = /<a id="(heading_\d+)"><\/a>/g
  const headings = []
  let m
  while ((m = headingRegex.exec(fullMd)) !== null) {
    headings.push({ id: m[1], pos: m.index })
  }
  console.log(`  Found ${headings.length} headings in Word document`)

  await fs.mkdir(IMAGES_DIR, { recursive: true })

  // Collect all unique image extraction rules across filtered sections
  const extractionRules = []
  for (const section of sections) {
    if (!section.images) continue
    for (const rule of section.images) {
      // Avoid duplicates (same headingId + name)
      if (!extractionRules.find(r => r.headingId === rule.headingId && r.name === rule.name)) {
        extractionRules.push(rule)
      }
    }
  }

  // Extract images for each rule
  /** @type {Map<string, string[]>} name → [filename, ...] */
  const imageMap = new Map()

  for (const rule of extractionRules) {
    const headingIdx = headings.findIndex(h => h.id === rule.headingId)
    if (headingIdx === -1) {
      console.warn(`  Warning: Heading ${rule.headingId} not found, skipping ${rule.name}`)
      imageMap.set(rule.name, [])
      continue
    }

    const startPos = headings[headingIdx].pos

    // Determine end position
    let endPos = fullMd.length
    if (rule.endHeadingId) {
      const endIdx = headings.findIndex(h => h.id === rule.endHeadingId)
      if (endIdx !== -1) endPos = headings[endIdx].pos
    } else if (headingIdx + 1 < headings.length) {
      endPos = headings[headingIdx + 1].pos
    }

    const sectionMd = fullMd.substring(startPos, endPos)

    // Extract and save base64 images
    const imgRegex = /!\[([^\]]*)\]\(data:image\/([^;]+);base64,([^)]+)\)/g
    let imgMatch
    let imageIndex = 0
    const imageFiles = []

    while ((imgMatch = imgRegex.exec(sectionMd)) !== null) {
      imageIndex++
      const ext = imgMatch[2] === 'x-emf' ? 'png' : imgMatch[2]
      const filename = `${rule.name}-${imageIndex}.${ext}`
      const filepath = path.join(IMAGES_DIR, filename)

      const buffer = Buffer.from(imgMatch[3], 'base64')
      await fs.writeFile(filepath, buffer)
      imageFiles.push(filename)
    }

    imageMap.set(rule.name, imageFiles)

    if (imageFiles.length > 0) {
      console.log(`  ${rule.name}: ${imageFiles.length} image(s)`)
    } else {
      console.log(`  ${rule.name}: no images found`)
    }
  }

  return imageMap
}

// ─── Step 2: Text Extraction (PDF → markdown) ──────────────────────────────

/**
 * Extract text from PDF using pdftotext with layout preservation.
 * The -layout flag preserves indentation which is critical for nested lists.
 */
function extractPdfText(pdfPath) {
  try {
    return execSync(`pdftotext -layout "${pdfPath}" -`, {
      encoding: 'utf-8',
      maxBuffer: 50 * 1024 * 1024,
    })
  } catch (err) {
    console.error('Error: pdftotext failed. Is poppler installed?')
    console.error('  Install with: brew install poppler')
    throw err
  }
}

/**
 * Find the position of a regex in fullText, starting search from afterPos.
 */
function findPatternPos(fullText, afterPos, pattern) {
  const remaining = fullText.substring(afterPos)
  const match = remaining.match(pattern)
  return match ? afterPos + match.index : fullText.length
}

/**
 * Convert raw PDF text (with layout indentation) into clean Markdown.
 *
 * pdftotext -layout indentation patterns:
 *   Numbered items:  "1.     Text" — col 0, text at ~col 7
 *   Sub-items:       "     a. Text" — 4-7 spaces before "a."
 *   Bullet points:   "   • Text" — indented with bullet char
 *   Sub-headings:    "2.2.1 Title" — section number + title → ## / ###
 */
function convertToMarkdown(rawText) {
  const lines = rawText.split('\n')
  const mdLines = []
  let current = ''
  let currentType = '' // 'num', 'sub', 'bullet', 'para'

  function flush() {
    if (current.trim()) {
      mdLines.push(current)
      current = ''
      currentType = ''
    }
  }

  function leadingSpaces(line) {
    const match = line.match(/^(\s*)/)
    return match ? match[1].length : 0
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trim()
    const indent = leadingSpaces(line)

    // Empty lines flush current block
    if (!trimmed) { flush(); continue }

    // Skip standalone page numbers
    if (/^\d+$/.test(trimmed)) continue

    // Sub-section headings: "2.2.1 Title" or "2.4.2.1 Title"
    const subHeadingMatch = trimmed.match(/^(\d+(?:\.\d+){2,})\s{1,3}(.+)/)
    if (subHeadingMatch && indent < 4) {
      flush()
      const depth = subHeadingMatch[1].split('.').length
      const prefix = depth <= 3 ? '##' : '###'
      mdLines.push(`\n${prefix} ${subHeadingMatch[2].trim()}\n`)
      continue
    }

    // Numbered list items: "1.  Text" at low indent
    const numberedMatch = trimmed.match(/^(\d+)\.\s{2,}(.*)/)
    if (numberedMatch && indent < 4) {
      flush()
      current = `${numberedMatch[1]}. ${numberedMatch[2]}`
      currentType = 'num'
      continue
    }

    // Sub-items: "a. Text" with 4+ spaces indent
    const subItemMatch = trimmed.match(/^([a-z])\.\s+(.*)/)
    if (subItemMatch && indent >= 4) {
      flush()
      current = `   ${subItemMatch[1]}. ${subItemMatch[2]}`
      currentType = 'sub'
      continue
    }

    // Bullet points: "•" or "·"
    const bulletMatch = trimmed.match(/^[•·]\s+(.*)/)
    if (bulletMatch) {
      flush()
      current = `- ${bulletMatch[1]}`
      currentType = 'bullet'
      continue
    }

    // Label lines: standalone labels like "FF Master:", "Type:", "Parameter"
    // Short lines at col 0 ending with ":" that aren't numbered items.
    // These must NOT be merged into the previous paragraph.
    // A blank line before the label ensures markdown renders it as a new paragraph
    // (otherwise it gets swallowed into the preceding list).
    if (trimmed.endsWith(':') && trimmed.length < 50 && indent < 4 && !/^\d/.test(trimmed)) {
      flush()
      mdLines.push('')
      mdLines.push(trimmed)
      continue
    }

    // Continuation lines
    if (current) {
      if (currentType === 'sub' && indent >= 4) { current += ' ' + trimmed; continue }
      if (currentType === 'num' && indent < 4) { current += ' ' + trimmed; continue }
      if (currentType === 'bullet' && indent >= 4) { current += ' ' + trimmed; continue }
      if (currentType === 'para') { current += ' ' + trimmed; continue }
    }

    // New paragraph
    flush()
    current = trimmed
    currentType = 'para'
  }
  flush()

  let result = mdLines.join('\n')
  result = result.replace(/\n{3,}/g, '\n\n')
  result = result.replace(/  +/g, ' ')
  return result.trim()
}

/**
 * Extract all section texts from PDF.
 * @param {typeof SECTIONS} sections — filtered sections to process
 * Returns a map: filename → markdown content (without images)
 */
function extractText(sections) {
  console.log('\n── Step 2: Extracting text from PDF ──')
  console.log('Reading:', PDF_PATH)

  const rawText = extractPdfText(PDF_PATH)
  const fullText = rawText.replace(/\f/g, '') // Strip form feeds from page boundaries
  console.log(`  Extracted: ${fullText.length} characters`)

  /** @type {Map<string, string>} file → markdown */
  const textMap = new Map()

  for (const section of sections) {
    const headingMatch = section.pattern.exec(fullText)
    if (!headingMatch) {
      console.warn(`  Warning: "${section.title}" not found, skipping ${section.file}`)
      continue
    }

    const startPos = headingMatch.index + headingMatch[0].length
    const endPos = findPatternPos(fullText, startPos, section.endBefore)
    const rawContent = fullText.substring(startPos, endPos)
    const mdContent = convertToMarkdown(rawContent)

    textMap.set(section.file, `# ${section.title}\n\n${mdContent}\n`)
    console.log(`  ${section.file}: ${mdContent.length} chars`)
  }

  return textMap
}

// ─── Step 3: Merge (text + images → final markdown) ────────────────────────

/**
 * Build markdown image reference lines for a list of filenames.
 */
function buildImageRefs(filenames, alts) {
  return filenames.map((f, i) => {
    const alt = alts && alts[i] ? alts[i] : ''
    return `![${alt}](/images/docx/${f})`
  }).join('\n\n')
}

/**
 * Insert image references into markdown text according to placement rules.
 */
function insertImages(markdown, section, imageMap) {
  if (!section.images || section.images.length === 0) return markdown

  let result = markdown

  for (const rule of section.images) {
    const filenames = imageMap.get(rule.name) || []
    if (filenames.length === 0) continue

    const refs = buildImageRefs(filenames, rule.alts)

    if (rule.position === 'start') {
      // Insert after the # title line
      const titleEnd = result.indexOf('\n\n')
      if (titleEnd !== -1) {
        result = result.substring(0, titleEnd + 2) + refs + '\n\n' + result.substring(titleEnd + 2)
      }
    } else if (rule.position === 'end') {
      // Append at end
      result = result.trimEnd() + '\n\n' + refs + '\n'
    } else if (rule.after) {
      // Find the target line and insert after it
      const lines = result.split('\n')
      const targetIdx = lines.findIndex(l => l.includes(rule.after))
      if (targetIdx !== -1) {
        // Find the end of the content block after this target line
        // For headings (## ...), insert right after the heading + next blank line
        // For text fragments, insert after that line + next blank line
        let insertIdx = targetIdx + 1

        // Skip any non-empty continuation lines after the target
        if (rule.after.startsWith('## ')) {
          // For headings: insert after the heading line itself
          // Find the next heading or end of content for this sub-section
          for (let j = targetIdx + 1; j < lines.length; j++) {
            if (lines[j].startsWith('## ') || lines[j].startsWith('# ')) {
              insertIdx = j
              break
            }
            insertIdx = j + 1
          }
          // Back up past trailing empty lines
          while (insertIdx > targetIdx + 1 && lines[insertIdx - 1].trim() === '') {
            insertIdx--
          }
        } else {
          // For text fragments: insert right after that line
          insertIdx = targetIdx + 1
        }

        lines.splice(insertIdx, 0, '', refs, '')
        result = lines.join('\n')
      } else {
        // Fallback: append at end if target not found
        console.warn(`    Warning: "${rule.after}" not found in ${section.file}, appending at end`)
        result = result.trimEnd() + '\n\n' + refs + '\n'
      }
    }
  }

  // Clean up excessive blank lines introduced by insertions
  result = result.replace(/\n{3,}/g, '\n\n')

  return result
}

/**
 * Merge text and images for all sections, write final markdown files.
 * @param {typeof SECTIONS} sections — filtered sections to process
 */
async function mergeAndWrite(textMap, imageMap, sections) {
  console.log('\n── Step 3: Merging text + images ──')

  await fs.mkdir(PAGES_DIR, { recursive: true })

  for (const section of sections) {
    const text = textMap.get(section.file)
    if (!text) continue

    const final = insertImages(text, section, imageMap)

    const outPath = path.join(PAGES_DIR, section.file)
    await fs.writeFile(outPath, final, 'utf-8')

    const imageCount = (section.images || []).reduce((sum, r) => {
      return sum + (imageMap.get(r.name) || []).length
    }, 0)
    const imageInfo = imageCount > 0 ? ` + ${imageCount} image(s)` : ''
    console.log(`  Written: ${section.file}${imageInfo}`)
  }
}

// ─── CLI ────────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2)
  const textOnly = args.includes('--text-only')
  const imagesOnly = args.includes('--images-only')

  // --chapter N: only process sections belonging to chapter N
  const chapterIdx = args.indexOf('--chapter')
  const chapterFilter = chapterIdx !== -1 ? Number(args[chapterIdx + 1]) : null

  // Filter sections by chapter if specified
  const sections = chapterFilter
    ? SECTIONS.filter(s => s.chapter === chapterFilter)
    : SECTIONS

  console.log('╔══════════════════════════════════════════════╗')
  console.log('║  Source-to-Markdown Conversion Pipeline      ║')
  console.log('║  PDF (text) + Word (images) → Markdown       ║')
  console.log('╚══════════════════════════════════════════════╝')

  if (chapterFilter) {
    console.log(`\n  Filtering: Chapter ${chapterFilter} only (${sections.length} sections)`)
  }

  if (imagesOnly) {
    // Images-only mode: extract images from Word, don't touch markdown
    const imageMap = await extractImages(sections)
    console.log('\n✓ Images extracted. Markdown files not modified.')
    return
  }

  // Full or text-only mode
  let imageMap = new Map()

  if (!textOnly) {
    // Step 1: Extract images from Word
    imageMap = await extractImages(sections)
  } else {
    console.log('\n── Skipping image extraction (--text-only) ──')
  }

  // Step 2: Extract text from PDF
  const textMap = extractText(sections)

  // Step 3: Merge and write
  await mergeAndWrite(textMap, imageMap, sections)

  console.log('\n✓ Done! Files written to src/content/pages/')
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})
