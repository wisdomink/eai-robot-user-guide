#!/usr/bin/env node
/**
 * pdf-to-md.mjs
 *
 * Converts the source PDF (manual.pdf) into per-section
 * Markdown files under src/content/pages/.
 *
 * Prerequisites:
 *   brew install poppler   (provides pdftotext, pdfimages)
 *
 * Usage:
 *   node scripts/pdf-to-md.mjs
 *
 * What it does:
 *   1. Reads src/content/source/manual.pdf via pdftotext -layout
 *   2. Splits by section heading patterns (e.g. "1.1 Safety Instructions")
 *   3. Converts indented text to proper Markdown with nested lists
 *   4. Extracts embedded images via pdfimages
 *   5. Writes individual .md files to src/content/pages/
 */

import { promises as fs } from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'

const ROOT = path.resolve(import.meta.dirname, '..')
const PDF_PATH = path.join(ROOT, 'src/content/source/manual.pdf')
const PAGES_DIR = path.join(ROOT, 'src/content/pages')
const IMAGES_DIR = path.join(ROOT, 'public/images/docx')

// Section definitions: regex pattern to match heading → { file, title }
// Patterns match the section numbering in the PDF (e.g. "1.1 Safety Instructions")
const SECTIONS = [
  { pattern: /^1\.1\s+Safety Instructions\s*$/m, file: 'safety-instructions.md', title: 'Safety Instructions' },
  { pattern: /^1\.2\s+Safety Guidelines\s*$/m, file: 'safety-guidelines.md', title: 'Safety Guidelines' },
  { pattern: /^1\.3\s+Maintenance and Management Guidelines\s*$/m, file: 'maintenance.md', title: 'Maintenance and Management Guidelines' },
  { pattern: /^2\.1\s+Packing List\s*$/m, file: 'packing-list.md', title: 'Packing List' },
  { pattern: /^2\.2\s+Product Overview\s*$/m, file: 'product-overview.md', title: 'Product Overview' },
  { pattern: /^2\.3\s+Computational Unit\s*$/m, file: 'computational-unit.md', title: 'Computational Unit' },
  { pattern: /^2\.4\s+Battery Indicator Lights\s*$/m, file: 'battery-indicator.md', title: 'Battery Indicator Lights' },
]

// All possible section heading patterns (used to detect section boundaries)
const ALL_HEADING_PATTERNS = [
  /^\d+\.\s+\S/m,        // Chapter headings: "1. Preliminary Notice"
  /^\d+\.\d+\s+\S/m,     // Section headings: "1.1 Safety Instructions"
]

/**
 * Extract text from PDF using pdftotext with layout preservation.
 * The -layout flag preserves indentation which is critical for nested lists.
 */
function extractText(pdfPath) {
  try {
    const text = execSync(`pdftotext -layout "${pdfPath}" -`, {
      encoding: 'utf-8',
      maxBuffer: 50 * 1024 * 1024,
    })
    return text
  } catch (err) {
    console.error('Error: pdftotext failed. Is poppler installed?')
    console.error('  Install with: brew install poppler')
    throw err
  }
}

/**
 * Find the position of each section heading in the full text.
 * Returns sorted array of { pattern, file, title, pos }.
 */
function findSectionPositions(fullText) {
  const positions = []

  for (const section of SECTIONS) {
    const match = section.pattern.exec(fullText)
    if (match) {
      positions.push({
        ...section,
        pos: match.index,
        matchEnd: match.index + match[0].length,
      })
    } else {
      console.warn(`  Warning: Section "${section.title}" not found in PDF text`)
    }
  }

  // Sort by position in document
  positions.sort((a, b) => a.pos - b.pos)
  return positions
}

/**
 * Find the next section/chapter heading after a given position.
 * This determines where a section's content ends.
 *
 * Section headings differ from numbered list items:
 * - Section headings: "1.3 Maintenance..." or "2. About FF Master" (1-2 spaces after number)
 * - List items:       "1.     Product Knowledge..." (5+ spaces after number)
 */
function findNextHeadingPos(fullText, afterPos) {
  const remaining = fullText.substring(afterPos)
  // Match sub-section headings like "1.3 Title" or chapter headings like "2. Title"
  // The key: section headings have 1-2 spaces; list items have 5+ spaces
  const headingMatch = remaining.match(/^(\d+\.\d+\s+[A-Z]|\d+\.\s{1,2}[A-Z])/m)
  if (headingMatch) {
    return afterPos + headingMatch.index
  }
  return fullText.length
}

/**
 * Convert raw PDF text (with layout indentation) into clean Markdown.
 *
 * pdftotext -layout indentation patterns observed:
 * - Numbered items: "1.     Text" — starts at col 0, text starts ~col 7
 * - Sub-items:      "     a. Text" — 4-7 spaces before "a."
 * - Continuation of numbered item: starts at col 0 (no indent)
 * - Continuation of sub-item: starts with ~4-5 spaces (indented)
 * - Bullet points:  "   • Text" — indented with bullet char
 */
function convertToMarkdown(rawText) {
  const lines = rawText.split('\n')
  const mdLines = []
  let current = ''     // current line being assembled
  let currentType = '' // 'num', 'sub', 'bullet', 'para'

  function flush() {
    if (current.trim()) {
      mdLines.push(current)
      current = ''
      currentType = ''
    }
  }

  /**
   * Measure leading whitespace of a raw line.
   */
  function leadingSpaces(line) {
    const match = line.match(/^(\s*)/)
    return match ? match[1].length : 0
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trimmed = line.trim()
    const indent = leadingSpaces(line)

    // Skip empty lines — flush current block
    if (!trimmed) {
      flush()
      continue
    }

    // Strip form feed characters (page breaks) but keep the rest of the line
    if (line.includes('\f')) {
      const cleaned = line.replace(/\f/g, '')
      if (!cleaned.trim()) continue
      // Re-process the cleaned line by replacing current line reference
      lines[i] = cleaned
      i--
      continue
    }

    // Skip standalone page numbers
    if (/^\d+$/.test(trimmed)) continue

    // --- Detect new numbered list items: "1.  Text" at low indent ---
    const numberedMatch = trimmed.match(/^(\d+)\.\s{2,}(.*)/)
    if (numberedMatch && indent < 4) {
      flush()
      current = `${numberedMatch[1]}. ${numberedMatch[2]}`
      currentType = 'num'
      continue
    }

    // --- Detect sub-items: "a. Text" with 4+ spaces indent ---
    const subItemMatch = trimmed.match(/^([a-z])\.\s+(.*)/)
    if (subItemMatch && indent >= 4) {
      flush()
      current = `   ${subItemMatch[1]}. ${subItemMatch[2]}`
      currentType = 'sub'
      continue
    }

    // --- Detect bullet points: "•" or "·" ---
    const bulletMatch = trimmed.match(/^[•·]\s+(.*)/)
    if (bulletMatch) {
      flush()
      current = `- ${bulletMatch[1]}`
      currentType = 'bullet'
      continue
    }

    // --- Continuation lines ---
    if (current) {
      // If we're in a sub-item and this line is also indented, it's a continuation
      if (currentType === 'sub' && indent >= 4) {
        current += ' ' + trimmed
        continue
      }
      // If we're in a numbered item and this line is at col 0, it's a continuation
      if (currentType === 'num' && indent < 4) {
        current += ' ' + trimmed
        continue
      }
      // If we're in a bullet and this line is indented, it's a continuation
      if (currentType === 'bullet' && indent >= 4) {
        current += ' ' + trimmed
        continue
      }
      // If we're in a paragraph, keep appending
      if (currentType === 'para') {
        current += ' ' + trimmed
        continue
      }
    }

    // --- Start a new plain paragraph ---
    flush()
    current = trimmed
    currentType = 'para'
  }

  flush()

  // Clean up the result
  let result = mdLines.join('\n')

  // Remove multiple consecutive blank lines
  result = result.replace(/\n{3,}/g, '\n\n')

  // Clean up double spaces
  result = result.replace(/  +/g, ' ')

  return result.trim()
}

async function main() {
  console.log('Reading:', PDF_PATH)

  // Check PDF exists
  try {
    await fs.access(PDF_PATH)
  } catch {
    console.error(`Error: PDF not found at ${PDF_PATH}`)
    process.exit(1)
  }

  // Extract text with layout preservation
  const fullText = extractText(PDF_PATH)
  console.log(`Extracted: ${fullText.length} characters of text`)

  // Find section positions
  const sections = findSectionPositions(fullText)
  console.log(`Found ${sections.length} sections`)

  // Create output directory
  await fs.mkdir(PAGES_DIR, { recursive: true })

  // Extract each section
  for (let i = 0; i < sections.length; i++) {
    const section = sections[i]

    // Section content starts after the heading line
    const startPos = section.matchEnd

    // Find end: the nearest heading boundary after our content starts.
    // This catches chapter headings (e.g. "2. About FF Master") that sit
    // between two of our tracked sub-sections.
    const nextTrackedPos = (i + 1 < sections.length) ? sections[i + 1].pos : fullText.length
    const nextAnyHeadingPos = findNextHeadingPos(fullText, startPos)
    const endPos = Math.min(nextTrackedPos, nextAnyHeadingPos)

    const rawContent = fullText.substring(startPos, endPos)

    // Convert to markdown
    const mdContent = convertToMarkdown(rawContent)

    // Assemble final file with title
    const finalMd = `# ${section.title}\n\n${mdContent}\n`

    const outPath = path.join(PAGES_DIR, section.file)
    await fs.writeFile(outPath, finalMd, 'utf-8')
    console.log(`  Written: ${section.file}`)
  }

  console.log('\nDone! Section files written to src/content/pages/')
}

main().catch(err => {
  console.error('Error:', err)
  process.exit(1)
})
